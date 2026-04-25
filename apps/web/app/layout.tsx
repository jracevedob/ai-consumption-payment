import type { ReactNode } from "react";
import "./globals.css";

export const metadata = {
  title: "Consumption Payment Index",
  description: "Real-time utility settlement over Lightning"
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

