export interface DownloadItem {
  id: string;
  name: string;
  downloaded_bytes: number;
  total_bytes: number;
  status: "downloading" | "finished" | "error";
  error?: string;
}

export interface Announcement {
  time: string;
  text: string;
  title?: string;
  urls?: string[];
  url?: string;
  versions?: string[] | string;
}

export interface UpdateInfo {
  version: string;
  currentVersion: string;
  title: string;
  body: string;
  releaseUrl: string;
  downloadUrl?: string;
  isPrerelease: boolean;
  publishedAt?: string;
}
