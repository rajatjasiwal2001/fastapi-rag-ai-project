import "./globals.css";

export const metadata = {
  title: "FastAPI RAG Chat",
  description: "Frontend for FastAPI RAG chatbot",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
