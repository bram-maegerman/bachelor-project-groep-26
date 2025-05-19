use pdfium_render::prelude::*;
use std::env;

fn main() {
    // Argument: path naar PDF-bestand
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("Gebruik: ocr_service <pad/naar/bestand.pdf>");
        std::process::exit(1);
    }

    let pdf_path = &args[1];
    let pdfium = Pdfium::new(Pdfium::bind_to_system_library().unwrap());

    let doc = pdfium.load_pdf_from_file(pdf_path, None).unwrap();
}


