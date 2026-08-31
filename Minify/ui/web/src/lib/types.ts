export interface DownloadItem {
  id: string;
  name: string;
  downloaded_bytes: number;
  total_bytes: number;
  status: "downloading" | "finished" | "error";
  error?: string;
}
