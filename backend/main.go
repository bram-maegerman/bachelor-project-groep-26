package main

import (
	"bytes"
	"fmt"
	"image"
	"image/jpeg"
	"log"
	"os"

	_ "image/jpeg"
	_ "image/png"
)

// Adjust contrast by modifying pixel values
// func adjustContrast(img image.Image, contrast float64) image.Image {
// 	// Create a new image with the same size and RGBA format
// 	bounds := img.Bounds()
// 	width, height := bounds.Max.X, bounds.Max.Y
// 	newImg := image.NewRGBA(bounds)

// 	// Adjust each pixel in the image
// 	for y := 0; y < height; y++ {
// 		for x := 0; x < width; x++ {
// 			originalColor := img.At(x, y)
// 			r, g, b, a := originalColor.RGBA()

// 			// Normalize RGB to [0, 1] and adjust contrast
// 			normalizedR := float64(r>>8) / 255.0
// 			normalizedG := float64(g>>8) / 255.0
// 			normalizedB := float64(b>>8) / 255.0

// 			// Apply contrast formula
// 			normalizedR = (normalizedR-0.5)*contrast + 0.5
// 			normalizedG = (normalizedG-0.5)*contrast + 0.5
// 			normalizedB = (normalizedB-0.5)*contrast + 0.5

// 			// Clamp values to [0, 1]
// 			if normalizedR > 1 {
// 				normalizedR = 1
// 			} else if normalizedR < 0 {
// 				normalizedR = 0
// 			}
// 			if normalizedG > 1 {
// 				normalizedG = 1
// 			} else if normalizedG < 0 {
// 				normalizedG = 0
// 			}
// 			if normalizedB > 1 {
// 				normalizedB = 1
// 			} else if normalizedB < 0 {
// 				normalizedB = 0
// 			}

// 			// Convert back to uint8 (0-255) and assign to the new image
// 			newColor := color.RGBA{
// 				R: uint8(normalizedR * 255),
// 				G: uint8(normalizedG * 255),
// 				B: uint8(normalizedB * 255),
// 				A: uint8(a >> 8),
// 			}

// 			newImg.Set(x, y, newColor)
// 		}
// 	}

// 	return newImg
// }

func main() {
	filePath := "./files/dankwoord.png"

	// Read the image file
	fileBytes, err := os.ReadFile(filePath)
	if err != nil {
		log.Fatal(err)
	}

	img, _, err := image.Decode(bytes.NewReader(fileBytes))
	if err != nil {
		log.Fatal(err)
	}

	// contrast := 5.0
	// adjustedImg := adjustContrast(img, contrast)

	outputFile, err := os.Create("output_image.jpg")
	if err != nil {
		log.Fatal(err)
	}
	defer outputFile.Close()

	// err = jpeg.Encode(outputFile, adjustedImg, nil)
	// if err != nil {
	// 	log.Fatal(err)
	// }

	fmt.Println("Contrast adjusted and saved to 'output_image.jpg'")
}
