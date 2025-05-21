import UploadFile from "./fileDropZone";
import Header from "./header"
import React, { useState } from "react";

export default function Home() {
  return (
    <>
      <Header />
      <UploadFile/>
    </>
  );
}
