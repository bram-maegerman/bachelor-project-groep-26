use lopdf::{Document, Object};
use std::error::Error;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::io::Write;
use std::sync::{Arc, Mutex};
use std::thread;

type Result<T> = std::result::Result<T, Box<dyn Error + Send + Sync>>;

fn main() -> Result<()> {
    // Parse command line arguments
    let args: Vec<String> = std::env::args().collect();
    if args.len() < 3 {
        eprintln!("Usage: {} <PDF file> <Page number>", args[0]);
        std::process::exit(1);
    }

    let pdf_path = &args[1];
    let page_number: u32 = match args[2].parse() {
        Ok(num) => num,
        Err(_) => {
            eprintln!("Error: Invalid page number '{}'", args[2]);
            std::process::exit(1);
        }
    };

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

    // Check if the requested page exists
    if !pages.contains_key(&page_number) {
        eprintln!("Error: Page {} not found in document", page_number);
        std::process::exit(1);
    }

    println!("--- Processing Page {} ---", page_number);

    // Get page object
    let page_id = pages[&page_number];
    let page_obj = match doc.get_object(page_id) {
        Ok(obj) => obj,
        Err(e) => {
            eprintln!("Error: Failed to get page object: {}", e);
            std::process::exit(1);
        }
    };

    // Get page dictionary
    let page_dict = match page_obj.as_dict() {
        Ok(dict) => dict,
        Err(_) => {
            eprintln!("Error: Page is not a valid dictionary");
            std::process::exit(1);
        }
    };

    // Get resources dictionary
    let resources_obj = match page_dict.get(b"Resources") {
        Ok(obj) => obj,
        Err(_) => {
            println!("No resources found for page {}", page_number);
            return Ok(());
        }
    };

    // Get XObject dictionary
    let resources_dict = match resources_obj.as_dict() {
        Ok(dict) => dict,
        Err(_) => {
            println!("Resources is not a valid dictionary");
            return Ok(());
        }
    };

    // Get XObject subdictionary
    let xobject_dict = match resources_dict.get(b"XObject").and_then(|obj| obj.as_dict()) {
        Ok(dict) => dict,
        Err(_) => {
            println!("No XObjects found on page {}", page_number);
            return Ok(());
        }
    };

    // If we have multiple images, process them in parallel
    let image_count = Arc::new(Mutex::new(0));
    let threads: Vec<_> = xobject_dict.iter()
        .filter_map(|(name, xobj_ref)| {
            // Only process references
            if let Object::Reference(obj_id) = xobj_ref {
                // Get the actual object
                match doc.get_object(*obj_id) {
                    Ok(xobject) => {
                        // Check if it's an image stream
                        if is_image_stream(&xobject) {
                            let name_str = std::str::from_utf8(name).unwrap_or("unnamed");
                            println!("Found image: {}", name_str);

                            // Track how many images we found
                            let mut count = image_count.lock().unwrap();
                            *count += 1;

                            // Clone necessary data for the thread
                            let xobject_clone = xobject.clone();
                            let output_dir = output_dir.clone();
                            let image_id = format!("{}_{}", page_number, name_str);

                            // Create thread
                            Some(thread::spawn(move || {
                                if let Err(e) = process_image(&xobject_clone, &image_id, &output_dir) {
                                    eprintln!("Error processing image {}: {}", image_id, e);
                                }
                            }))
                        } else {
                            None
                        }
                    }
                    Err(_) => None,
                }
            } else {
                None
            }
        })
        .collect();

    // Wait for all threads to complete
    for thread in threads {
        let _ = thread.join();
    }

    let total_images = *image_count.lock().unwrap();
    println!("Processed {} images from page {}", total_images, page_number);

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
fn process_image(image_obj: &Object, image_id: &str, output_dir: &Path) -> Result<()> {
    if let Object::Stream(ref stream) = image_obj {
        // Get raw image data
        let raw_bytes = &stream.content;

        // Create path for OCR output
        let output_base = output_dir.join(image_id);
        let output_path = output_base.to_string_lossy().to_string();

        // Run tesseract OCR
        let mut tesseract = Command::new("tesseract")
            .arg("-")
            .arg(&output_path)
            .arg("--oem")
            .arg("3")
            .arg("--psm")
            .arg("6")
            .stdin(std::process::Stdio::piped())
            .stdout(std::process::Stdio::piped())
            .stderr(std::process::Stdio::piped())
            .spawn()?;

        // Write image data to tesseract's stdin
        {
            let stdin = tesseract.stdin.as_mut().ok_or("Failed to open stdin")?;
            stdin.write_all(raw_bytes)?;
        }

        // Wait for tesseract to finish
        let output = tesseract.wait_with_output()?;

        if output.status.success() {
            // Read OCR result
            let text_file_path = format!("{}.txt", output_path);
            match std::fs::read_to_string(&text_file_path) {
                Ok(text) => {
                    let trimmed_text = text.trim();
                    if !trimmed_text.is_empty() {
                        println!("Text from image {}: {}", image_id, trimmed_text);
                    } else {
                        println!("No text extracted from image {}", image_id);
                    }
                },
                Err(e) => {
                    println!("Could not read OCR output file for {}: {}", image_id, e);
                }
            }
        } else {
            let stderr = String::from_utf8_lossy(&output.stderr);
            return Err(format!("Tesseract failed: {}", stderr).into());
        }
    }

    Ok(())
}