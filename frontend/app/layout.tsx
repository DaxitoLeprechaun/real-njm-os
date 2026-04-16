import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/njm/Sidebar";
import { Toaster } from "sonner";

export const metadata: Metadata = {
  title: "NJM OS — Agentic Operating System",
  description: "NJM Agents Workspace",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es" className="dark">
      <body className="antialiased">
        {/* Nature background layer */}
        <div
          className="fixed inset-0 -z-10 bg-cover bg-center"
          style={{
            backgroundImage: "url('/nature-bg.jpg')",
            opacity: 0.08,
          }}
        />
        {/* Background fill so glass composites correctly */}
        <div className="fixed inset-0 -z-20 bg-background" />

        <div className="flex min-h-screen">
          <Sidebar />
          <main className="flex-1 ml-[240px] min-h-screen">
            {children}
          </main>
        </div>
        <Toaster position="bottom-right" theme="dark" richColors />
      </body>
    </html>
  );
}
