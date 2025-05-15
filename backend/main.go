package main

import "github.com/otiai10/gosseract/v2"

/**
*  @Author: elliott
*  @Date: 2024/2/29
*  @Desc:
 */

func GetImageInfo(img []byte) (string, error) {
	client := gosseract.NewClient()
	defer client.Close()
	client.SetImageFromBytes(img)
	text, _ := client.Text()
	return text, nil
}