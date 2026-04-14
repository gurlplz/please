/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Xenova transformers loads WASM / ONNX assets from node_modules at runtime
  serverExternalPackages: ["@xenova/transformers", "onnxruntime-node"],
  webpack: (config) => {
    config.resolve.alias = {
      ...config.resolve.alias,
      // Optional peers pulled in by WalletConnect / MetaMask SDK paths
      "@react-native-async-storage/async-storage": false,
      "pino-pretty": false
    };
    return config;
  },
  experimental: {
    serverActions: {
      bodySizeLimit: "2mb"
    }
  }
};

export default nextConfig;
