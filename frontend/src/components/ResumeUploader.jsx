// components/ResumeUploader.jsx — Drag-and-drop PDF/DOCX uploader
import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, X, CheckCircle } from 'lucide-react';

export default function ResumeUploader({ onFileSelect, disabled = false }) {
  const [file, setFile] = useState(null);

  const onDrop = useCallback((accepted) => {
    if (accepted.length > 0) {
      setFile(accepted[0]);
      onFileSelect(accepted[0]);
    }
  }, [onFileSelect]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    maxFiles: 1,
    disabled,
  });

  const removeFile = (e) => {
    e.stopPropagation();
    setFile(null);
    onFileSelect(null);
  };

  return (
    <div>
      <div
        {...getRootProps()}
        style={{
          border: `2px dashed ${isDragActive ? 'var(--accent)' : file ? 'var(--success)' : 'var(--border)'}`,
          borderRadius: 'var(--radius-lg)',
          padding: '32px 20px',
          textAlign: 'center',
          cursor: disabled ? 'not-allowed' : 'pointer',
          background: isDragActive
            ? 'var(--accent-glow)'
            : file
            ? 'var(--success-bg)'
            : 'rgba(255,255,255,0.02)',
          transition: 'all 0.25s ease',
          opacity: disabled ? 0.55 : 1,
        }}
      >
        <input {...getInputProps()} id="resume-upload-input" />

        {file ? (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12 }}>
            <CheckCircle size={24} color="var(--success)" />
            <div style={{ textAlign: 'left' }}>
              <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.9rem' }}>
                {file.name}
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                {(file.size / 1024).toFixed(1)} KB
              </div>
            </div>
            <button
              onClick={removeFile}
              style={{
                marginLeft: 8, padding: 4, background: 'var(--danger-bg)',
                border: 'none', borderRadius: 6, cursor: 'pointer', color: 'var(--danger)',
                display: 'flex', alignItems: 'center',
              }}
            >
              <X size={14} />
            </button>
          </div>
        ) : (
          <div>
            <div style={{
              width: 52, height: 52,
              background: 'var(--gradient-main)',
              borderRadius: 12, margin: '0 auto 14px',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              boxShadow: 'var(--shadow-btn)',
            }}>
              <Upload size={22} color="#fff" />
            </div>
            <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: 6 }}>
              {isDragActive ? 'Drop your resume here' : 'Drop your resume or click to upload'}
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Supports PDF and DOCX · Max 16MB
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
