import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Lazarius Video AI',
  description: 'Open-source AI video generation studio',
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="fr"><body>{children}</body></html>;
}
