use lopdf::{Document, Object};
use std::error::Error;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::io::Write;
use std::sync::{Arc, Mutex};

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

    // Track total images processed
    let total_images = Arc::new(Mutex::new(0));

    // Process each page
    for (&page_number, &page_id) in pages.iter() {
        println!("--- Processing Page {} ---", page_number);

        // Get page object
        let page_obj = match doc.get_object(page_id) {
            Ok(obj) => obj,
            Err(e) => {
                eprintln!("Error: Failed to get page object for page {}: {}", page_number, e);
                continue;
            }
        };

        // Get page dictionary
        let page_dict = match page_obj.as_dict() {
            Ok(dict) => dict,
            Err(_) => {
                eprintln!("Error: Page {} is not a valid dictionary", page_number);
                continue;
            }
        };

        // Get resources dictionary
        let resources_obj = match page_dict.get(b"Resources") {
            Ok(obj) => obj,
            Err(_) => {
                println!("No resources found for page {}", page_number);
                continue;
            }
        };

        // Get XObject dictionary
        let resources_dict = match resources_obj.as_dict() {
            Ok(dict) => dict,
            Err(_) => {
                println!("Resources is not a valid dictionary for page {}", page_number);
                continue;
            }
        };

        // Get XObject subdictionary
        let xobject_dict = match resources_dict.get(b"XObject").and_then(|obj| obj.as_dict()) {
            Ok(dict) => dict,
            Err(_) => {
                println!("No XObjects found on page {}", page_number);
                continue;
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

                            // Track how many images we found
                            let mut count = total_images.lock().unwrap();
                            *count += 1;

                            let image_id = page_number.to_string();

                            // Process image directly without threading
                            if let Err(e) = process_image(&xobject, &image_id, &output_dir) {
                                eprintln!("Error processing image {}: {}", image_id, e);
                            }
                        }
                    }
                    Err(e) => {
                        eprintln!("Error: {}", e);
                    }
                }
            }
        }
    }
    Ok(())
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
fn process_image(image_obj: &Object, image_id: &str, _output_dir: &Path) -> Result<()> {
    match image_obj {
        Object::Stream(stream) => {
            // Extract raw image data
            let raw_bytes = &stream.content;

            // Load image from raw bytes
            let img = image::load_from_memory(raw_bytes)
                .map_err(|e| format!("Failed to load image from memory: {}", e))?;

            // Process the image
            let processed_image = process_image_section(img, "img")?;

            // Print results if available
            if let Some(text) = processed_image {
                println!("Header text from image {}: {}", image_id, text);
            } else {
                println!("No text extracted from header of image {}", image_id);
            }

            Ok(())
        },
        _ => Err("Object is not a stream".into())
    }
}

/// Helper function to process a section of an image (header or footer)
fn process_image_section(
    img: image::DynamicImage,
    section_name: &str
) -> Result<Option<String>> {
    // Convert the image to raw bytes
    let mut image_bytes = Vec::new();
    {
        let mut cursor = std::io::Cursor::new(&mut image_bytes);
        img.write_to(&mut cursor, image::ImageFormat::Png)
            .map_err(|e| format!("Failed to encode {}: {}", section_name, e))?;
    }

    // Run tesseract OCR on the image without writing to disk
    run_tesseract(&image_bytes, section_name)
}

/// Run the tesseract OCR process and capture output directly
fn run_tesseract(image_bytes: &[u8], section_name: &str) -> Result<Option<String>> {
    // Use stdout directly for output instead of writing to a file
    let mut tesseract = Command::new("tesseract")
        .arg("-")  // Read from stdin
        .arg("stdout")  // Output to stdout instead of a file
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
    {
        let stdin = tesseract.stdin.as_mut()
            .ok_or_else(|| "Failed to open stdin".to_string())?;
        stdin.write_all(image_bytes)
            .map_err(|e| format!("Failed to write to tesseract: {}", e))?;
    }

    // Wait for tesseract to finish
    let output = tesseract.wait_with_output()
        .map_err(|e| format!("Failed to wait for tesseract: {}", e))?;

    // Check if tesseract succeeded
    if output.status.success() {
        // Process stdout directly instead of reading from a file
        let text = String::from_utf8_lossy(&output.stdout).to_string();
        let trimmed_text = text;

        if !trimmed_text.is_empty() {
            Ok(Some(trimmed_text.to_string()))
        } else {
            Ok(None)
        }
    } else {
        let stderr = String::from_utf8_lossy(&output.stderr);
        Err(format!("Tesseract failed on {}: {}", section_name, stderr).into())
    }
}