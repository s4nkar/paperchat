import { Upload } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function PdfUploader() {
  return (
    <Button variant="outline" className="w-full gap-2 font-medium">
      <Upload className="h-4 w-4" />
      Upload PDFs
    </Button>
  );
}
