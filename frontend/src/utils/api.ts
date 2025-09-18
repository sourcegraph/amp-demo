import { ProductType } from "../context/GlobalState";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8001";

export const api = {
  async getFeaturedProducts(limit: number = 5): Promise<ProductType[]> {
    const response = await fetch(`${API_BASE_URL}/products/featured?limit=${limit}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  },

  async getPopularProducts(limit: number = 10): Promise<ProductType[]> {
    const response = await fetch(`${API_BASE_URL}/products/popular?limit=${limit}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  },

  async getAllProducts(): Promise<ProductType[]> {
    const response = await fetch(`${API_BASE_URL}/products`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  }
};
