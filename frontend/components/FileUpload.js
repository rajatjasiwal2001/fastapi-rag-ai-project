"use client";

import { useRef, useState } from "react";
import axios from "axios";

const API_BASE_URL = "http://127.0.0.1:8000";

export default function FileUpload() {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [status, setStatus] = useState({ type: "", message: "" });
  const fileInputRef = useRef(null);

  const uploadFile = async (file) => {
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      setIsUploading(true);
      setStatus({ type: "", message: "" });

      await axios.post(`${API_BASE_URL}/upload`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
        timeout: 120000,
      });

      setStatus({ type: "success", message: "Document uploaded and indexed." });
    } catch (error) {
      const message =
        (error?.code === "ECONNABORTED"
          ? "Upload timed out. Backend may still be loading the embedding model."
          : null) ||
        error?.response?.data?.detail ||
        "Upload failed. Please check your backend and try again.";
      setStatus({ type: "error", message });
    } finally {
      setIsUploading(false);
    }
  };

  const handleDrop = async (event) => {
    event.preventDefault();
    setIsDragging(false);
    const file = event.dataTransfer.files?.[0];
    await uploadFile(file);
  };

  return (
    <div className="rounded-2xl bg-white p-5 shadow-md">
      <h2 className="mb-3 text-lg font-semibold">Upload Document</h2>
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        className={`flex min-h-36 cursor-pointer items-center justify-center rounded-xl border-2 border-dashed p-4 text-center transition ${
          isDragging ? "border-blue-500 bg-blue-50" : "border-gray-300 bg-gray-50"
        }`}
        onClick={() => fileInputRef.current?.click()}
      >
        {isUploading ? (
          <p className="text-sm text-gray-600">Uploading...</p>
        ) : (
          <p className="text-sm text-gray-600">
            Drag and drop a file here, or click to choose.
          </p>
        )}
      </div>

      <input
        ref={fileInputRef}
        type="file"
        className="hidden"
        onChange={(e) => uploadFile(e.target.files?.[0])}
      />

      {status.message && (
        <p
          className={`mt-3 text-sm ${
            status.type === "success" ? "text-green-600" : "text-red-600"
          }`}
        >
          {status.message}
        </p>
      )}
    </div>
  );
}
