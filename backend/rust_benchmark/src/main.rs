use lopdf::{Document, Object};
use std::error::Error;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::io::Write;
use std::collections::HashMap;
use regex::Regex;

type Result<T> = std::result::Result<T, Box<dyn Error + Send + Sync>>;

fn main() -> Result<()> {
    // Parse command line arguments
    let args: Vec<String> = std::env::args().collect();
    if args.len() < 2 {
        eprintln!("Usage: {} <PDF file>", args[0]);
        std::process::exit(1);
    }

    let pdf_path = &args[1];

    // Setup output directory
    let output_dir = PathBuf::from("../files/images");
    if !output_dir.exists() {
        std::fs::create_dir_all(&output_dir)?;
    }

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
    println!("Found {} pages in the document", pages.len());

    // Create array of HashMaps to store numbers and Roman numerals for each page
    let mut number_collections: Vec<HashMap<String, usize>> = vec![HashMap::new(); pages.len()];

    // Prepare regex patterns for numbers and Roman numerals
    let num_pattern = Regex::new(r"\b\d+\b").unwrap();
    let roman_pattern = Regex::new(r"(?i)\bM{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})\b").unwrap();

    // Process each page
    let mut results: Vec<Result<HashMap<String, usize>>> = Vec::with_capacity(pages.len());
    for (&page_number, &page_id) in pages.iter() {
        println!("--- Processing Page {} ---", page_number);
        let result = process_page(&doc, page_number, page_id, &output_dir, &num_pattern, &roman_pattern);
        results.push(result);
        if page_number == 5 {
            println!("--- Stopping after processing page 5 ---");
            break;
        }
    }

    // Aggregate results into the number_collections
    for (page_idx, result) in results.into_iter().enumerate() {
        if let Ok(page_numbers) = result {
            let page_num = pages.keys().nth(page_idx).unwrap_or(&0);
            let idx = (*page_num as usize) - 1;
            // Store the results in our array of hashmaps at index page_number - 1
            if idx < number_collections.len() {
                number_collections[idx] = page_numbers;
            }
        }
    }

    // Output the collected numbers and Roman numerals
    for (page_idx, numbers) in number_collections.iter().enumerate() {
        println!("Page {}: Found {} unique numbers and Roman numerals", page_idx + 1, numbers.len());
        if !numbers.is_empty() {
            let keys = numbers.keys();
            let formatted = keys
                .map(|k| k.to_string())  // convert each key to String
                .collect::<Vec<_>>()
                .join(", ");
            println!("  Values: {{{}}}", formatted);  // print with curly braces
     }
    }

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
    let page_obj = match doc.get_object(page_id) {
        Ok(obj) => obj,
        Err(e) => {
            eprintln!("Error: Failed to get page object for page {}: {}", page_number, e);
            return Ok(page_numbers);
        }
    };

    // Get page dictionary
    let page_dict = match page_obj.as_dict() {
        Ok(dict) => dict,
        Err(_) => {
            eprintln!("Error: Page {} is not a valid dictionary", page_number);
            return Ok(page_numbers);
        }
    };

    // Get resources dictionary
    let resources_obj = match page_dict.get(b"Resources") {
        Ok(obj) => obj,
        Err(_) => {
            println!("No resources found for page {}", page_number);
            return Ok(page_numbers);
        }
    };

    // Get XObject dictionary
    let resources_dict = match resources_obj.as_dict() {
        Ok(dict) => dict,
        Err(_) => {
            println!("Resources is not a valid dictionary for page {}", page_number);
            return Ok(page_numbers);
        }
    };

    // Get XObject subdictionary
    let xobject_dict = match resources_dict.get(b"XObject").and_then(|obj| obj.as_dict()) {
        Ok(dict) => dict,
        Err(_) => {
            println!("No XObjects found on page {}", page_number);
            return Ok(page_numbers);
        }
    };

    // Process each image on the page
    for (_name, xobj_ref) in xobject_dict.iter() {
        // Only process references
        if let Object::Reference(obj_id) = xobj_ref {
            // Get the actual object
            match doc.get_object(*obj_id) {
                Ok(xobject) => {
                    // Check if it's an image stream
                    if is_image_stream(&xobject) {
                        let image_id = page_number.to_string();

                        // Process image and extract text
                        match process_image(&xobject, &image_id, output_dir) {
                            Ok(Some(text)) => {
                                println!("Text from image {}: {}", image_id, text);

                                // Extract numbers and Roman numerals from the text
                                extract_numbers_and_romans(&text, &mut page_numbers, num_pattern, roman_pattern);
                            }
                            Ok(None) => {
                                println!("No text extracted from image {}", image_id);
                            }
                            Err(e) => {
                                eprintln!("Error processing image {}: {}", image_id, e);
                            }
                        }
                    }
                }
                Err(e) => {
                    eprintln!("Error: {}", e);
                }
            }
        }
    }

    // Also check for text content on the page if available
    if let Ok(contents) = page_dict.get(b"Contents") {
        if let Ok(text) = extract_text_from_contents(contents, doc) {
            extract_numbers_and_romans(&text, &mut page_numbers, num_pattern, roman_pattern);
        }
    }

    Ok(page_numbers)
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
                            // Since decode_stream is not available, we'll use a simpler approach
                            // This is a simplified text extraction
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
        // Capture the number
        let number = capture.as_str().trim().to_string();
        if !number.is_empty() {
            *page_numbers.entry(number).or_insert(0) += 1;
        }
    }

    // Find and collect Roman numerals
    for capture in roman_pattern.find_iter(text) {
        let roman = capture.as_str().trim().to_string();
        if !roman.is_empty() {
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
fn process_image(image_obj: &Object, image_id: &str, _output_dir: &Path) -> Result<Option<String>> {
    match image_obj {
        Object::Stream(stream) => {
            // Check if we have a filter that's compatible
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

            // Try to load image from raw bytes - wrap in a proper error handling
            let img = match image::load_from_memory(raw_bytes) {
                Ok(img) => img,
                Err(e) => {
                    eprintln!("Warning: Failed to load image {}: {}", image_id, e);
                    return Ok(None);
                }
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
    run_tesseract(&image_bytes, section_name)
}

/// Run the tesseract OCR process and capture output directly
fn run_tesseract(image_bytes: &[u8], section_name: &str) -> Result<Option<String>> {
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
        .stderr(std::process::Stdio::piped())
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

        if !trimmed_text.is_empty() {
            Ok(Some(trimmed_text))
        } else {
            Ok(None)
        }
    } else {
        let stderr = String::from_utf8_lossy(&output.stderr);
        Err(format!("Tesseract failed on {}: {}", section_name, stderr).into())
    }
}