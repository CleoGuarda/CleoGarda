import { NextConfig } from 'next'
import withTM from 'next-transpile-modules'

const config: NextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  experimental: { esmExternals: true },
  images: {
    domains: ['assets.example.com', 'images.example.org'],
  },
  rewrites() {
    return [
      { source: '/api/:path*', destination: '*' },
    ]
  },
}

export default withTM(config, {
  transpileModules: [ '@ai-sdk/openai'],
})
