/**
 * WHY THIS DESIGN WAS CHOSEN:
 * The ResumeViewer component is optimized for a mobile-first responsive experience.
 * On viewports smaller than 768px, the toolbar controls wrap vertically and the action
 * buttons are expanded to 44px (h-11) height to satisfy mobile touch target guidelines.
 * The PDF viewport utilizes `justify-start md:justify-center` alongside `overflow-x-auto`
 * to allow users to scroll horizontally and read the full-width document at a legible scale,
 * avoiding the need to scale/shrink the PDF which severely compromises readability.
 */
"use client";

import { useState, useEffect } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import { getResumeUrl } from "@/services/api/portfolio";
import { Download, Printer, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { StatusState } from "@/components/common/StatusState";

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
      <div className="flex flex-col sm:flex-row w-full items-center justify-between p-3 gap-3 sm:gap-0 rounded-xl border border-border bg-card/45 backdrop-blur-sm">
        <div className="text-xs text-muted-foreground font-medium">
          {numPages ? `Page ${pageNumber} of ${numPages}` : "Loading Document..."}
        </div>
        <div className="flex w-full sm:w-auto gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handlePrint}
            className="flex-1 sm:flex-initial h-11 sm:h-7 px-4 sm:px-2.5 gap-1.5 text-xs font-semibold cursor-pointer"
            disabled={loading || !!error}
          >
            <Printer className="h-3.5 w-3.5" />
            Print
          </Button>
          <a href={pdfUrl} download="Ajay_Susanth_Resume.pdf" className="flex-1 sm:flex-initial">
            <Button
              variant="default"
              size="sm"
              className="w-full h-11 sm:h-7 px-4 sm:px-2.5 gap-1.5 text-xs font-semibold cursor-pointer"
              disabled={loading || !!error}
            >
              <Download className="h-3.5 w-3.5" />
              Download PDF
            </Button>
          </a>
        </div>
      </div>

      {/* PDF Screen Viewport */}
      <div className="w-full flex justify-start md:justify-center p-4 border border-border bg-muted/20 rounded-2xl overflow-auto min-h-[500px] relative">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-background/50 z-10">
            <div className="flex flex-col items-center space-y-2">
              <Loader2 className="h-8 w-8 text-primary animate-spin" />
              <span className="text-xs text-muted-foreground font-medium">Rendering resume pages...</span>
            </div>
          </div>
        )}

        {error ? (
          <StatusState
            type="error"
            title="Preview Rendering Unavailable"
            description="Your browser security sandboxing or network policies blocked PDF.js canvas generation. You can still download the resume file directly to view or print it."
            onRetry={() => {
              setError(null);
              setLoading(true);
            }}
            retryText="Reload Viewer"
          />
        ) : (
          pdfUrl && (
            <Document
              file={pdfUrl}
              onLoadSuccess={onDocumentLoadSuccess}
              onLoadError={onDocumentLoadError}
              loading=""
              className="shadow-md border border-border/40 rounded-lg overflow-hidden shrink-0"
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

