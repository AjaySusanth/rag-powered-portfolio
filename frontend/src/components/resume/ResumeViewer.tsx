"use client";

import { useState, useEffect } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import { getResumeUrl } from "@/services/api/portfolio";
import { Download, Printer, Loader2, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

// Configure local CDN worker source
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

export default function ResumeViewer() {
  const [numPages, setNumPages] = useState<number | null>(null);
  const [pageNumber, setPageNumber] = useState<number>(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pdfUrl, setPdfUrl] = useState<string>("");

  useEffect(() => {
    setPdfUrl(getResumeUrl());
  }, []);

  function onDocumentLoadSuccess({ numPages }: { numPages: number }) {
    setNumPages(numPages);
    setLoading(false);
  }

  function onDocumentLoadError(err: Error) {
    console.error("react-pdf error:", err);
    setError(err.message);
    setLoading(false);
  }

  const handlePrint = () => {
    if (typeof window !== "undefined") {
      const printWindow = window.open(pdfUrl, "_blank");
      if (printWindow) {
        printWindow.focus();
        printWindow.print();
      }
    }
  };

  return (
    <div className="flex flex-col items-center w-full space-y-4">
      {/* Toolbar Actions */}
      <div className="flex w-full items-center justify-between p-3 rounded-xl border border-border bg-card/45 backdrop-blur-sm">
        <div className="text-xs text-muted-foreground font-medium">
          {numPages ? `Page ${pageNumber} of ${numPages}` : "Loading Document..."}
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handlePrint}
            className="gap-1.5 text-xs font-semibold cursor-pointer"
            disabled={loading || !!error}
          >
            <Printer className="h-3.5 w-3.5" />
            Print
          </Button>
          <a href={pdfUrl} download="Ajay_Susanth_Resume.pdf">
            <Button
              variant="default"
              size="sm"
              className="gap-1.5 text-xs font-semibold cursor-pointer"
              disabled={loading || !!error}
            >
              <Download className="h-3.5 w-3.5" />
              Download PDF
            </Button>
          </a>
        </div>
      </div>

      {/* PDF Screen Viewport */}
      <div className="w-full flex justify-center p-4 border border-border bg-muted/20 rounded-2xl overflow-auto min-h-[500px] relative">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-background/50 z-10">
            <div className="flex flex-col items-center space-y-2">
              <Loader2 className="h-8 w-8 text-primary animate-spin" />
              <span className="text-xs text-muted-foreground font-medium">Rendering resume pages...</span>
            </div>
          </div>
        )}

        {error ? (
          <div className="flex flex-col items-center justify-center p-6 text-center space-y-3">
            <AlertCircle className="h-8 w-8 text-rose-500" />
            <h3 className="text-sm font-bold text-foreground">Preview Rendering Unavailable</h3>
            <p className="text-xs text-muted-foreground max-w-sm">
              Your browser security sandboxing or network policies blocked PDF.js canvas generation. You can still download the resume file directly to view or print it.
            </p>
            <a href={pdfUrl} download="Ajay_Susanth_Resume.pdf">
              <Button size="sm" className="gap-1.5 font-semibold">
                <Download className="h-3.5 w-3.5" />
                Download Resume
              </Button>
            </a>
          </div>
        ) : (
          pdfUrl && (
            <Document
              file={pdfUrl}
              onLoadSuccess={onDocumentLoadSuccess}
              onLoadError={onDocumentLoadError}
              loading=""
              className="shadow-md border border-border/40 rounded-lg overflow-hidden"
            >
              <Page
                pageNumber={pageNumber}
                scale={1.25}
                renderTextLayer={false}
                renderAnnotationLayer={false}
                loading=""
              />
            </Document>
          )
        )}
      </div>
    </div>
  );
}
