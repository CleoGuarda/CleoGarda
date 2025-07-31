import { NextConfig } from 'next'
import withTM from 'next-transpile-modules'

const withTranspile = withTM({
  transpileModules: ['@ai-sdk/openai'],
})

const nextConfig: NextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  experimental: {
    esmExternals: true,
  },
  images: {
    domains: ['assets.example.com', 'images.example.org'],
    formats: ['image/avif', 'image/webp'],
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        // proxy through internal API handler
        destination: '/api-proxy/:path*',
      },
    ]
  },
  i18n: {
    locales: ['en', 'ru'],
    defaultLocale: 'en',
  },
  webpack(config) {
    // prevent process.browser deprecation warnings
    config.resolve.fallback = { ...(config.resolve.fallback || {}), fs: false }
    return config
  },
}

export default withTranspile(nextConfig)
