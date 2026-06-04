import '@/styles/globals.css';
import type { AppProps } from 'next/app';
import Link from 'next/link';
import { useRouter } from 'next/router';

function Nav() {
  const { pathname } = useRouter();
  const link = (href: string, label: string) => (
    <Link
      href={href}
      className={`text-sm font-medium transition-colors ${
        pathname === href
          ? 'text-gray-900'
          : 'text-gray-400 hover:text-gray-700'
      }`}
    >
      {label}
    </Link>
  );

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 h-11 bg-white border-b border-gray-100 flex items-center px-6 gap-6">
      <Link href="/" className="text-sm font-bold text-gray-900 tracking-tight mr-2">
        Lattice
      </Link>
      {link('/', 'Studio')}
      {link('/atlas', 'Atlas')}
    </nav>
  );
}

export default function App({ Component, pageProps }: AppProps) {
  return (
    <>
      <Nav />
      <div className="pt-11">
        <Component {...pageProps} />
      </div>
    </>
  );
}
