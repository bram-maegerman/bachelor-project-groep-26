use lopdf::{Document, Object};
use std::error::Error;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::io::Write;
use std::collections::HashMap;
use regex::Regex;
use rayon::prelude::*; // Add Rayon for parallelism

type Result<T> = std::result::Result<T, Box<dyn Error + Send + Sync>>;

fn main() -> Result<()> {
    // Parse command line arguments
    let args: Vec<String> = std::env::args().collect();
    if args.len() < 2 {
        eprintln!("Usage: {} <PDF file>", args[0]);
        std::process::exit(1);
    }

    let pdf_path = &args[1];

    // Setup output directory - create only if needed during image processing
    let output_dir = PathBuf::from("../files/images");

    // Validate PDF file exists
    let pdf_file = Path::new(pdf_path);
    if !pdf_file.exists() {
        eprintln!("Error: PDF file does not exist: {}", pdf_path);
        std::process::exit(1);
    }

    // Load the PDF document
    let doc = match Document::load(pdf_path) {
        Ok(doc) => doc,
        Err(e) => {
            eprintln!("Error: Failed to open PDF file: {}", e);
            std::process::exit(1);
        }
    };

    let pages = doc.get_pages();
    let page_count = pages.len(); // Process at most 10 pages
    
    // Create a shared reference to the document and patterns for all threads
    let doc = std::sync::Arc::new(doc);
    let output_dir = std::sync::Arc::new(output_dir);
    let num_pattern = std::sync::Arc::new(Regex::new(r"\b\d+\b").unwrap());
    let roman_pattern = std::sync::Arc::new(Regex::new(r"(?i)\bM{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})\b").unwrap());

    // Convert pages to a vector of (page_number, page_id) for parallel processing
    let page_data: Vec<(u32, lopdf::ObjectId)> = pages.iter()
        .take(page_count)
        .map(|(&page_number, &page_id)| (page_number, page_id))
        .collect();

    // Process pages in parallel using Rayon
    let number_collections: Vec<HashMap<String, usize>> = page_data.par_iter()
        .map(|(page_number, page_id)| {
            let doc = doc.clone();
            let output_dir = output_dir.clone();
            let num_pattern = num_pattern.clone();
            let roman_pattern = roman_pattern.clone();
            
            process_page(&doc, *page_number, *page_id, &output_dir, &num_pattern, &roman_pattern)
                .unwrap_or_else(|_| HashMap::new())
        })
        .collect();

    // Create a complete vector with empty hashmaps for missing pages
    let mut final_collections = vec![HashMap::new(); page_count];
    for (i, page_data) in page_data.iter().enumerate() {
        let page_idx = (page_data.0 as usize) - 1;
        if page_idx < final_collections.len() {
            final_collections[page_idx] = number_collections[i].clone();
        }
    }

    // Print results in the requested format
    print!("[");
    for (i, numbers) in final_collections.iter().enumerate() {
        if i > 0 {
            print!(", ");
        }
        
        // Format: {num1, num2, ...} - even for empty hashmaps
        let keys: Vec<&String> = numbers.keys().collect();
        let joined = keys.iter().map(|s| s.as_str()).collect::<Vec<&str>>().join(", ");
        print!("{{{}}}", joined);
    }
    println!("]");

    Ok(())
}

/// Process a single page of the PDF
fn process_page(
    doc: &Document,
    page_number: u32,
    page_id: lopdf::ObjectId,
    output_dir: &Path,
    num_pattern: &Regex,
    roman_pattern: &Regex,
) -> Result<HashMap<String, usize>> {
    let mut page_numbers: HashMap<String, usize> = HashMap::new();

    // Get page object
    let page_obj = doc.get_object(page_id)
        .map_err(|e| format!("Failed to get page object for page {}: {}", page_number, e))?;

    // Get page dictionary
    let page_dict = page_obj.as_dict()
        .map_err(|_| format!("Page {} is not a valid dictionary", page_number))?;

    // Try to extract text from page contents
    if let Ok(contents) = page_dict.get(b"Contents") {
        if let Ok(text) = extract_text_from_contents(contents, doc) {
            extract_numbers_and_romans(&text, &mut page_numbers, num_pattern, roman_pattern);
        }
    }

    // Try to process images if resources exist
    if let Ok(resources_obj) = page_dict.get(b"Resources") {
        if let Ok(resources_dict) = resources_obj.as_dict() {
            // Only proceed with XObject if it exists
            if let Ok(xobject) = resources_dict.get(b"XObject") {
                if let Ok(xobject_dict) = xobject.as_dict() {
                    process_xobjects(doc, xobject_dict, output_dir, &mut page_numbers, num_pattern, roman_pattern)?;
                }
            }
        }
    }

    Ok(page_numbers)
}

/// Process XObjects (images) in a page - now with potential for parallelism
fn process_xobjects(
    doc: &Document,
    xobject_dict: &lopdf::Dictionary,
    output_dir: &Path,
    page_numbers: &mut HashMap<String, usize>,
    num_pattern: &Regex,
    roman_pattern: &Regex,
) -> Result<()> {
    // Create output directory only if needed
    if !xobject_dict.is_empty() && !output_dir.exists() {
        std::fs::create_dir_all(output_dir)?;
    }

    // Collect all image objects that need to be processed
    let mut image_objects = Vec::new();
    for (_name, xobj_ref) in xobject_dict.iter() {
        // Only process references
        if let Object::Reference(obj_id) = xobj_ref {
            // Get the actual object
            if let Ok(xobject) = doc.get_object(*obj_id) {
                // Check if it's an image stream
                if is_image_stream(&xobject) {
                    image_objects.push(xobject.clone());
                }
            }
        }
    }

    // Process images in parallel for this page
    if !image_objects.is_empty() {
        let output_dir = output_dir.to_path_buf();
        
        // We can use Rayon's par_iter here as well
        let texts: Vec<Option<String>> = image_objects.par_iter()
            .map(|xobject| {
                process_image(xobject, &output_dir).unwrap_or(None)
            })
            .collect();
        
        // Process all extracted texts
        for maybe_text in texts {
            if let Some(text) = maybe_text {
                extract_numbers_and_romans(&text, page_numbers, num_pattern, roman_pattern);
            }
        }
    }
    
    Ok(())
}

/// Extract text from page contents if possible
fn extract_text_from_contents(contents: &Object, doc: &Document) -> Result<String> {
    let mut text = String::new();

    match contents {
        Object::Array(arr) => {
            for item in arr {
                if let Object::Reference(ref_id) = item {
                    if let Ok(obj) = doc.get_object(*ref_id) {
                        if let Object::Stream(stream) = obj {
                            if let Ok(content_str) = String::from_utf8(stream.content.clone()) {
                                text.push_str(&content_str);
                            }
                        }
                    }
                }
            }
        },
        Object::Reference(ref_id) => {
            if let Ok(obj) = doc.get_object(*ref_id) {
                if let Object::Stream(stream) = obj {
                    if let Ok(content_str) = String::from_utf8(stream.content.clone()) {
                        text.push_str(&content_str);
                    }
                }
            }
        },
        _ => {}
    }

    Ok(text)
}

/// Extract numbers and Roman numerals from text
fn extract_numbers_and_romans(
    text: &str,
    page_numbers: &mut HashMap<String, usize>,
    num_pattern: &Regex,
    roman_pattern: &Regex
) {
    // Find and collect regular numbers
    for capture in num_pattern.find_iter(text) {
        let number = capture.as_str().trim().to_string();
        if !number.is_empty() {
            *page_numbers.entry(number).or_insert(0) += 1;
        }
    }

    // Find and collect Roman numerals
    for capture in roman_pattern.find_iter(text) {
        let raw = capture.as_str().trim();
        if !raw.is_empty() {
            let roman = format!("\"{}\"", raw);
            *page_numbers.entry(roman).or_insert(0) += 1;
        }
    }
}

/// Check if an object is an image stream
fn is_image_stream(obj: &Object) -> bool {
    if let Object::Stream(ref stream) = obj {
        if let Ok(subtype) = stream.dict.get(b"Subtype") {
            if let Ok(subtype_name) = subtype.as_name() {
                return subtype_name == b"Image";
            }
        }
    }
    false
}

/// Process a single image - extract and run OCR
fn process_image(image_obj: &Object, output_dir: &Path) -> Result<Option<String>> {
    match image_obj {
        Object::Stream(stream) => {
            // Check if we have a compatible filter
            let mut is_compatible = true;
            if let Ok(filter) = stream.dict.get(b"Filter") {
                // Some filters might need special handling
                if let Ok(filter_name) = filter.as_name() {
                    if filter_name != b"DCTDecode" && filter_name != b"FlateDecode" {
                        is_compatible = false;
                    }
                }
            }

            if !is_compatible {
                return Ok(None);
            }

            // Extract raw image data
            let raw_bytes = &stream.content;

            // Try to load image from raw bytes
            let img = match image::load_from_memory(raw_bytes) {
                Ok(img) => img,
                Err(_) => return Ok(None),
            };

            // Process the image and run OCR
            process_image_section(img, "img")
        },
        _ => Err("Object is not a stream".into())
    }
}

/// Helper function to process a section of an image
fn process_image_section(
    img: image::DynamicImage,
    section_name: &str
) -> Result<Option<String>> {
    // Convert the image to raw bytes for tesseract
    let mut image_bytes = Vec::new();
    {
        let mut cursor = std::io::Cursor::new(&mut image_bytes);
        img.write_to(&mut cursor, image::ImageFormat::Png)
            .map_err(|e| format!("Failed to encode {}: {}", section_name, e))?;
    }

    // Run tesseract OCR on the image
    run_tesseract(&image_bytes)
}

/// Run the tesseract OCR process and capture output directly
fn run_tesseract(image_bytes: &[u8]) -> Result<Option<String>> {
    // Use stdout directly for output instead of writing to a file
    let mut tesseract = Command::new("tesseract")
        .arg("-")  // Read from stdin
        .arg("stdout")  // Output to stdout
        .arg("--oem")
        .arg("3")  // Use LSTM OCR engine
        .arg("--psm")
        .arg("6")  // Assume a single uniform block of text
        .stdin(std::process::Stdio::piped())
        .stdout(std::process::Stdio::piped())
        .stderr(std::process::Stdio::null())  // Discard stderr for clean output
        .spawn()
        .map_err(|e| format!("Failed to spawn tesseract: {}", e))?;

    // Write image data to tesseract's stdin
    if let Some(mut stdin) = tesseract.stdin.take() {
        stdin.write_all(image_bytes)
            .map_err(|e| format!("Failed to write to tesseract: {}", e))?;
        // Explicitly drop stdin to close it
        drop(stdin);
    } else {
        return Err("Failed to open stdin".into());
    }

    // Wait for tesseract to finish
    let output = tesseract.wait_with_output()
        .map_err(|e| format!("Failed to wait for tesseract: {}", e))?;

    // Check if tesseract succeeded
    if output.status.success() {
        // Process stdout
        let text = String::from_utf8_lossy(&output.stdout).to_string();
        let trimmed_text = text.trim().to_string();
        let lines: Vec<_> = trimmed_text.lines().collect();
        let line_count = lines.len();
        let mut selected_lines = Vec::new();
        if line_count >= 1 {
            selected_lines.push(lines[0]);
        }
        if line_count >= 2 {
            selected_lines.push(lines[1]);
        }

        // Add last two lines if they exist (and they're different from first two)
        if line_count >= 3 && line_count - 2 >= 2 { // Ensure we don't duplicate lines
            selected_lines.push(lines[line_count - 2]);
        }
        if line_count >= 4 && line_count - 1 >= 2 { // Ensure we don't duplicate lines
            selected_lines.push(lines[line_count - 1]);
        }

        // Join selected lines back into a single string
        let extracted_text = selected_lines.join(" ");
        let cleaned_text = extracted_text
                            .replace("Vv", "v")
                            .replace("Ii", "i")
                            .replace("Xx", "x")
                            .replace("Ll", "l")
                            .replace("Cc", "c")
                            .replace("Dd", "d")
                            .replace("Mm", "m");
                            
        // Remove debug print to improve performance
        // println!("{}",cleaned_text);
        
        if !cleaned_text.is_empty() {
            Ok(Some(cleaned_text))
        } else {
            Ok(None)
        }
    } else {
        Ok(None)  // Silently handle tesseract failures
    }
}