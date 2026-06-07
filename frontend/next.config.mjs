/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: "standalone", // smaller Docker image
  eslint: {
    // ESLint is run separately in CI (npm run lint)
    ignoreDuringBuilds: true,
  },
  typescript: {
    // Type checking is run separately in CI (npm run typecheck)
    ignoreBuildErrors: true,
  },
};
export default nextConfig;
