use lopdf::{Document, Object};
use std::error::Error;
use std::process::Command;
use std::io::Write;

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
            // Get the raw bytes of the image in utf-8
            let raw_bytes_str = &stream.content;

            // use the raw bytes as stdinput for tesseract without saving it to a file
            let mut tesseract = Command::new("tesseract")
                .arg("-") // Use "-" to read from stdin
                .arg(format!("../files/images/image_{}", obj_id)) // Output file path
                .arg("--oem")
                .arg("3") // Use LSTM OCR engine
                .arg("--psm")
                .arg("6") // Assume a single uniform block of text
                .stdin(std::process::Stdio::piped())
                .spawn()?;

            // Write the raw bytes to tesseract's stdin
            {
                let stdin = tesseract.stdin.as_mut().expect("Failed to open stdin");
                stdin.write(raw_bytes_str)?;
            }
            // Wait for tesseract to finish
            let output = tesseract.wait_with_output()?;

            // Check if the command succeeded
            if output.status.success() {
                // Read the generated text file (tesseract adds .txt extension)
                let text_file_path = format!("../files/images/image_{}.txt", obj_id);
                let text = std::fs::read_to_string(&text_file_path)?;

                // Print the extracted text
                println!("Extracted text from image {}: {}", obj_id, text);
            } else {
                // If tesseract failed, return an error
                let error_message = String::from_utf8_lossy(&output.stderr);
                return Err(format!("Tesseract failed: {}", error_message).into());
            }
        }
        _ => {
            println!("Not a stream");
        }
    }

    Ok(())
}