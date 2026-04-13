import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Linq Alert System",
  description: "Real-time crypto alert infrastructure dashboard",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
