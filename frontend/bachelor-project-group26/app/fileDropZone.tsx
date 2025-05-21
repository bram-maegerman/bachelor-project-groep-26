
"use client";
import React, { useState, useEffect } from "react";
import Dropzone from "react-dropzone";

const UploadFile = () => {
  const [file, setFile] = useState(null);

  const handleUpload = (acceptedFiles: any) => {
    console.log("logging drop/selected file",acceptedFiles);
    const url = "https://api.escuelajs.co/api/v1/files/upload";
    const formData = new FormData();
    formData.append("file", acceptedFiles[0]);

    fetch(url, {
      method: "POST",
      body: formData,
    })
      .then((response) => {
        if (response.ok) {
          // File uploaded successfully
          console.log(formData)
          setFile(acceptedFiles[0]);
        } else {
          // File upload failed
          console.error(response);
        }
      })
      .catch((error) => {
        console.error(error);
      });
  };

  useEffect(() => {
    console.log(file)
  }, [file])

  return (
    <div className="main-container">
      <Dropzone onDrop={handleUpload} accept="image/*" minSize={1024} maxSize={3072000}>
        {({ getRootProps, getInputProps, isDragActive, isDragAccept, isDragReject }: any) => {
          const additionalClass = isDragAccept ? "accept" : isDragReject ? "reject" : "";

          return (
            <div
              {...getRootProps({
                className: `dropzone ${additionalClass}`,
              })}
            >
              <input {...getInputProps()} />
              <p>Drag'n'drop images, or click to select files</p>
            </div>
          );
        }}
      </Dropzone>
      {file && (
        <>
        <p>{file[0]}</p>
          <h4>File Uploaded Successfully !!</h4>
          <img src={URL.createObjectURL(file)} className="img-container" alt="Uploaded file" />
        </>
      )}
    </div>
  );
};

export default UploadFile;