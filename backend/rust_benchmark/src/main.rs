use lopdf::{Document, Object};
use std::error::Error;
use std::process::Command;

fn main() -> Result<(), Box<dyn Error>> {
    // Expect a path as an argument
    let args: Vec<String> = std::env::args().collect();
    if args.len() < 3 {
        eprintln!("Usage: {} <PDF file> <Page number>", args[0]);
        std::process::exit(1);
    }
    // Check if the output directory exists
    let output_dir = "../files/images";
    if !std::path::Path::new(output_dir).exists() {
        std::fs::create_dir_all(output_dir)?;
    }
    // Check if the PDF file exists
    if !std::path::Path::new(&args[1]).exists() {
        eprintln!("PDF file does not exist: {}", args[1]);
        std::process::exit(1);
    }



    // Load the PDF document, checking for errors
    let doc = Document::load(&args[1]).expect("Failed to open PDF file");


    let pages = doc.get_pages();

    // Get the page number from the command line argument and parse it to u32
    let page_number: u32 = args[2].parse().expect("Invalid page number");


    if let Some(page_id) = pages.get(&page_number) {
        println!("--- Page {} ---", page_number);

        let page_obj = doc.get_object(*page_id).expect("Failed to get page object");

        let page_dict = page_obj.as_dict().expect("Page is not a dictionary");

        match page_dict.get(b"Resources") {
            Ok(resources_obj) => {
                // Parse the resources object as a dictionary
                if let Ok(resources_dict) = resources_obj.as_dict() {
                    // Get the XObject subdictionary
                    if let Ok(xobject_dict) = resources_dict.get(b"XObject").and_then(|obj| obj.as_dict()) {
                        // Iterate through all XObjects (images, forms, etc.)
                        for (name, xobject_ref) in xobject_dict.iter() {
                            // Follow the reference to get the actual object
                            match xobject_ref {
                                Object::Reference(obj_id) => {
                                    match doc.get_object(*obj_id) {
                                        Ok(xobject) => {
                                            // Handle both stream objects and dictionary objects
                                            match xobject {
                                                Object::Stream(ref stream) => {
                                                    // For stream objects, check the dictionary part of the stream
                                                    let stream_dict = &stream.dict;
                                                    match stream_dict.get(b"Subtype") {
                                                        Ok(subtype) => {
                                                            match subtype.as_name() {
                                                                Ok(subtype_name) => {
                                                                    if subtype_name == b"Image" {
                                                                        println!("Found image: {:?}", std::str::from_utf8(name).unwrap_or("invalid"));
                                                                        let _ = extract_image_data(page_number, &xobject);

                                                                        // Extract text from the saved image
                                                                        let image_filename = format!("../files/images/image_{}.jpg", page_number);
                                                                        let _ = extract_text_from_image(&image_filename, &page_number.to_string());
                                                                    } else {
                                                                        println!("Not an image, subtype is: {:?}", std::str::from_utf8(subtype_name).unwrap_or("invalid"));
                                                                    }
                                                                }
                                                                Err(e) => println!("Failed to get subtype name: {:?}", e),
                                                            }
                                                        }
                                                        Err(e) => println!("No Subtype field found in stream: {:?}", e),
                                                    }
                                                }
                                                _ => println!("Not a stream"),
                                            }
                                        }
                                        Err(e) => println!("Failed to get object: {:?}", e),
                                    }
                                }
                                _ => println!("XObject not a reference"),
                            }
                        }
                    }
                }
            }
            Err(_) => {
                println!("No resources found for page {}", page_number);
            }
        }

    }

    Ok(())
}

fn extract_image_data(obj_id: u32, image_obj: &Object) -> Result<(), Box<dyn Error>> {
    match image_obj {
        Object::Stream(ref stream) => {
            // Get image properties from the stream's dictionary
            let dict = &stream.dict;

            // Get filter information
            match dict.get(b"Filter") {
                Ok(filter) => {
                    match filter.as_name() {
                        Ok(filter_name) => {
                            println!("Filter: {:?}", std::str::from_utf8(filter_name)?);

                            // The stream contains the compressed image data
                            let stream_data = &stream.content;

                            match filter_name {
                                b"DCTDecode" => {
                                    // JPEG image - you can save this directly
                                    std::fs::write(format!("../files/images/image_{}.jpg", obj_id), stream_data)?;
                                    println!("Saved JPEG image as image_{}.jpg", obj_id);
                                }
                                b"FlateDecode" => {
                                    // Compressed data - needs decompression
                                    println!("Found FlateDecode image (needs decompression)");
                                    // You would need to decompress with flate/zlib and then interpret based on ColorSpace, etc.
                                }
                                _ => {
                                    println!("Unsupported filter: {:?}", std::str::from_utf8(filter_name)?);
                                }
                            }
                        }
                        Err(e) => println!("Filter is not a name: {:?}", e),
                    }
                }
                Err(e) => println!("No Filter field found: {:?}", e),
            }
        }
        _ => {
            println!("Image object is not a stream");
        }
    }

    Ok(())
}

fn extract_text_from_image(image_path: &str, page_number: &str) -> Result<(), Box<dyn Error>> {
    // Create the output path for the text file
    let output_path = format!("../files/images/image_{}", page_number);

    // Run tesseract command
    let output = Command::new("tesseract")
        .arg(image_path)          // Input image path
        .arg(&output_path)        // Output file path (without extension)
        // OEM and PSM options
        .arg("--oem")
        .arg("3")                // Use LSTM OCR engine
        .arg("--psm")
        .arg("6")                // Assume a single uniform block of text
        .output()?;               // Execute and get output

    // Check if the command succeeded
    if output.status.success() {
        // Read the generated text file (tesseract adds .txt extension)
        let text_file_path = format!("{}.txt", output_path);  // Fixed path construction
        std::fs::read_to_string(&text_file_path)?;

        // Remove the image file after processing
        std::fs::remove_file(image_path)?;

        // Return the text without printing anything
        Ok(())
    } else {
        // If tesseract failed, return an error
        let error_message = String::from_utf8_lossy(&output.stderr);
        Err(format!("Tesseract failed: {}", error_message).into())
    }
}