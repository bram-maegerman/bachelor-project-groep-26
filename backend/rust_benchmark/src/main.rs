use tesseract::Tesseract;
use pdfium_render::prelude::*;
use std::env;
use std::fs;
use std::path::Path;

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
    let mut ocr_engine = LepTess::new(None, "eng").unwrap();

    for (i, page) in doc.pages().iter().enumerate() {
        let bitmap = page.render().render().unwrap();

        let png_path = format!("page_{}.png", i + 1);
        bitmap.as_image().save(&png_path).unwrap();

        ocr_engine.set_image(&png_path);
        let text = ocr_engine.get_utf8_text().unwrap();

        println!("--- Pagina {} ---\n{}", i + 1, text);
        fs::remove_file(png_path).unwrap();
    }
}


