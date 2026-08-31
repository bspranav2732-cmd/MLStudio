import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Solvosys - Machine Learning Research Workbench',
  description: 'Enterprise & Academic Machine Learning Platform',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen antialiased selection:bg-[#ff4b4b] selection:text-white" style={{ backgroundColor: 'var(--bg)', color: 'var(--text-primary)' }}>
        {children}
      </body>
    </html>
  );
}
