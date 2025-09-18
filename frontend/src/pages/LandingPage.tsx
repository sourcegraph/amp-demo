import { FC, useEffect, useState } from "react";
import {
  VStack,
  Text,
  Heading,
  SimpleGrid,
  Box,
  HStack,
  Tag,
  Button,
  useBreakpointValue,
} from "@chakra-ui/react";
import { useNavigate } from "react-router-dom";
import Main from "../components/Main";
import HeroCarousel from "../components/HeroCarousel";
import ProductCard from "../components/ProductCard";
import ProductsGrid from "../components/ProductsGrid";
import LoadingProduct from "../components/Loading/LoadingProduct";
import { useGlobalContext } from "../context/useGlobalContext";
import { ProductType } from "../context/GlobalState";
import { api } from "../utils/api";

const LandingPage: FC = () => {
  const { addToCart } = useGlobalContext();
  const [popularProducts, setPopularProducts] = useState<ProductType[]>([]);
  const [isLoadingPopular, setIsLoadingPopular] = useState(true);
  const navigate = useNavigate();

  // Responsive grid columns
  const categoryColumns = useBreakpointValue({ base: 2, md: 4 });

  useEffect(() => {
    const fetchPopularProducts = async () => {
      try {
        const products = await api.getPopularProducts(8);
        setPopularProducts(products);
      } catch (error) {
        console.error("Failed to fetch popular products:", error);
        setPopularProducts([]);
      } finally {
        setIsLoadingPopular(false);
      }
    };

    fetchPopularProducts();
  }, []);

  const categories = [
    { name: "Electronics", emoji: "📱", color: "blue" },
    { name: "Clothing", emoji: "👕", color: "purple" },
    { name: "Jewelry", emoji: "💍", color: "yellow" },
    { name: "Home & Garden", emoji: "🏡", color: "green" },
  ];

  const handleCategoryClick = (categoryName: string) => {
    navigate(`/search/${categoryName.toLowerCase()}`);
  };

  const searchTags = [
    "trending",
    "sale",
    "new arrivals",
    "bestsellers",
    "gifts",
    "fashion",
    "tech",
    "accessories"
  ];

  return (
    <Main>
      {/* Hero Carousel */}
      <Box mb={8}>
        <HeroCarousel onAddToCart={addToCart} />
      </Box>

      {/* Category Navigation */}
      <VStack spacing={6} mb={8}>
        <Heading size="lg" color="gray.700">
          Shop by Category
        </Heading>
        <SimpleGrid columns={categoryColumns} spacing={4} w="full">
          {categories.map((category, index) => (
            <Box
              key={index}
              p={6}
              bg="white"
              borderRadius="lg"
              boxShadow="sm"
              border="1px solid"
              borderColor="gray.200"
              cursor="pointer"
              onClick={() => handleCategoryClick(category.name)}
              _hover={{
                transform: "translateY(-4px)",
                boxShadow: "lg",
                borderColor: `${category.color}.300`,
              }}
              transition="all 0.2s"
              textAlign="center"
            >
              <Text fontSize="3xl" mb={2}>
                {category.emoji}
              </Text>
              <Text fontWeight="semibold" color="gray.700">
                {category.name}
              </Text>
            </Box>
          ))}
        </SimpleGrid>
      </VStack>

      {/* Search Tags */}
      <VStack spacing={4} mb={8}>
        <HStack spacing={2} flexWrap="wrap" justify="center">
          <Text fontWeight="bold" fontSize="sm" color="gray.600">
            Popular:
          </Text>
          {searchTags.map((tag, index) => (
            <Tag
              key={index}
              size="sm"
              bg="gray.100"
              color="gray.700"
              borderRadius="full"
              cursor="pointer"
              _hover={{ bg: "blue.100", color: "blue.700" }}
              onClick={() => navigate(`/search/${tag}`)}
            >
              {tag}
            </Tag>
          ))}
        </HStack>
      </VStack>

      {/* Popular Products Section */}
      <VStack spacing={6} align="stretch">
        <Box textAlign="center">
          <Heading size="lg" color="gray.700" mb={2}>
            Popular Right Now
          </Heading>
          <Text color="gray.600">
            Discover what everyone's talking about
          </Text>
        </Box>

        <ProductsGrid>
          {isLoadingPopular
            ? Array(8)
                .fill("")
                .map((_, i) => <LoadingProduct key={i} />)
            : popularProducts.map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
        </ProductsGrid>

        {/* View All Products Button */}
        <Box textAlign="center" mt={6}>
          <Button
            colorScheme="blue"
            size="lg"
            onClick={() => navigate("/products")}
            _hover={{
              transform: "translateY(-2px)",
              boxShadow: "lg",
            }}
          >
            View All Products
          </Button>
        </Box>
      </VStack>
    </Main>
  );
};

export default LandingPage;
