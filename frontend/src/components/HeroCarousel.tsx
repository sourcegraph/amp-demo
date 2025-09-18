import { FC, useEffect, useState } from "react";
import {
  Box,
  Button,
  Text,
  VStack,
  HStack,
  IconButton,
  useBreakpointValue,
} from "@chakra-ui/react";
import { ChevronLeftIcon, ChevronRightIcon } from "@chakra-ui/icons";
import { motion, AnimatePresence } from "framer-motion";
import { ProductType, getImageUrl } from "../context/GlobalState";
import { api } from "../utils/api";
import { useNavigate } from "react-router-dom";

const MotionBox = motion(Box);

interface HeroCarouselProps {
  onAddToCart?: (product: ProductType) => void;
}

const HeroCarousel: FC<HeroCarouselProps> = ({ onAddToCart }) => {
  const [featuredProducts, setFeaturedProducts] = useState<ProductType[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  // Responsive height
  const carouselHeight = useBreakpointValue({ base: "300px", md: "400px", lg: "500px" });

  useEffect(() => {
    const fetchFeaturedProducts = async () => {
      try {
        const products = await api.getFeaturedProducts(5);
        setFeaturedProducts(products);
      } catch (error) {
        console.error("Failed to fetch featured products:", error);
        // Fallback to empty array
        setFeaturedProducts([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchFeaturedProducts();
  }, []);

  // Auto-advance carousel every 6 seconds
  useEffect(() => {
    if (featuredProducts.length === 0) return;

    const interval = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % featuredProducts.length);
    }, 6000);

    return () => clearInterval(interval);
  }, [featuredProducts.length]);

  const handlePrevious = () => {
    setCurrentIndex((prev) => 
      prev === 0 ? featuredProducts.length - 1 : prev - 1
    );
  };

  const handleNext = () => {
    setCurrentIndex((prev) => (prev + 1) % featuredProducts.length);
  };

  const handleProductClick = (product: ProductType) => {
    navigate(`/products/${product.id}`);
  };

  if (isLoading) {
    return (
      <Box 
        height={carouselHeight} 
        bg="gray.100" 
        display="flex" 
        alignItems="center" 
        justifyContent="center"
        borderRadius="md"
      >
        <Text>Loading featured products...</Text>
      </Box>
    );
  }

  if (featuredProducts.length === 0) {
    return (
      <Box 
        height={carouselHeight} 
        bg="gray.50" 
        display="flex" 
        alignItems="center" 
        justifyContent="center"
        borderRadius="md"
      >
        <Text color="gray.600">No featured products available</Text>
      </Box>
    );
  }

  const currentProduct = featuredProducts[currentIndex];

  return (
    <Box position="relative" height={carouselHeight} borderRadius="md" overflow="hidden">
      <AnimatePresence mode="wait">
        <MotionBox
          key={currentIndex}
          initial={{ opacity: 0, x: 300 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -300 }}
          transition={{ duration: 0.5 }}
          position="absolute"
          top={0}
          left={0}
          right={0}
          bottom={0}
          backgroundImage={`linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.3)), url(${getImageUrl(currentProduct)})`}
          backgroundSize="cover"
          backgroundPosition="center"
          display="flex"
          alignItems="center"
          justifyContent="center"
          color="white"
        >
          <VStack spacing={4} textAlign="center" maxW="2xl" px={8}>
            <Text 
              fontSize={{ base: "2xl", md: "4xl", lg: "5xl" }} 
              fontWeight="bold" 
              textShadow="2px 2px 4px rgba(0,0,0,0.5)"
              lineHeight="shorter"
            >
              {currentProduct.title}
            </Text>
            <Text 
              fontSize={{ base: "md", md: "lg" }} 
              maxW="md"
              textShadow="1px 1px 2px rgba(0,0,0,0.5)"
              noOfLines={2}
            >
              {currentProduct.description}
            </Text>
            <Text 
              fontSize={{ base: "xl", md: "2xl" }} 
              fontWeight="bold" 
              color="yellow.300"
              textShadow="1px 1px 2px rgba(0,0,0,0.5)"
            >
              ${currentProduct.price}
            </Text>
            <HStack spacing={4}>
              <Button
                colorScheme="blue"
                size={{ base: "md", md: "lg" }}
                onClick={() => handleProductClick(currentProduct)}
                _hover={{ transform: "translateY(-2px)", boxShadow: "lg" }}
              >
                View Product
              </Button>
              {onAddToCart && (
                <Button
                  colorScheme="green"
                  variant="outline"
                  size={{ base: "md", md: "lg" }}
                  onClick={() => onAddToCart(currentProduct)}
                  bg="whiteAlpha.200"
                  borderColor="green.300"
                  color="white"
                  _hover={{ 
                    bg: "green.500", 
                    borderColor: "green.500",
                    transform: "translateY(-2px)",
                    boxShadow: "lg" 
                  }}
                >
                  Add to Cart
                </Button>
              )}
            </HStack>
          </VStack>
        </MotionBox>
      </AnimatePresence>

      {/* Navigation arrows */}
      <IconButton
        aria-label="Previous product"
        icon={<ChevronLeftIcon />}
        position="absolute"
        left={4}
        top="50%"
        transform="translateY(-50%)"
        colorScheme="whiteAlpha"
        variant="solid"
        size="lg"
        onClick={handlePrevious}
        _hover={{ bg: "whiteAlpha.300" }}
      />
      <IconButton
        aria-label="Next product"
        icon={<ChevronRightIcon />}
        position="absolute"
        right={4}
        top="50%"
        transform="translateY(-50%)"
        colorScheme="whiteAlpha"
        variant="solid"
        size="lg"
        onClick={handleNext}
        _hover={{ bg: "whiteAlpha.300" }}
      />

      {/* Indicators */}
      <HStack 
        position="absolute" 
        bottom={4} 
        left="50%" 
        transform="translateX(-50%)"
        spacing={2}
      >
        {featuredProducts.map((_, index) => (
          <Box
            key={index}
            w={3}
            h={3}
            borderRadius="full"
            bg={index === currentIndex ? "white" : "whiteAlpha.500"}
            cursor="pointer"
            onClick={() => setCurrentIndex(index)}
            transition="all 0.2s"
            _hover={{ bg: "white" }}
          />
        ))}
      </HStack>
    </Box>
  );
};

export default HeroCarousel;
