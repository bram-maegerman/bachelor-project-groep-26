use lopdf::{Document};

fn main() {
    let path = "../../files/DIGI_2007_000118_01.pdf"; 
    let doc = Document::load(path).expect("Failed to open PDF file");
}
