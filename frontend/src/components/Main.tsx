import {
  Box,
  Flex,
  FormControl,
  FormLabel,
  HStack,
  Select,
  TabList,
  Tabs,
  useMediaQuery,
} from "@chakra-ui/react";
import { ReactNode } from "react";
import { useLocation } from "react-router-dom";
import { useGlobalContext } from "../context/useGlobalContext";
import MUIBadge from "./MUI/MUIBadge";
import Tab from "./Tab";

type Props = {
  children: ReactNode;
};

const Main = ({ children }: Props) => {
  const { 
    savedItemsCount, 
    products, 
    categoryFilter, 
    priceSort, 
    nameSort,
    setCategoryFilter,
    setPriceSort,
    setNameSort
  } = useGlobalContext();
  const [isLargerThan567] = useMediaQuery("(min-width: 567px)");
  const location = useLocation();

  // Get unique categories from products
  const categories = Array.from(
    new Set(
      products.map(product => 
        typeof product.category === 'string' 
          ? product.category 
          : product.category?.name
      ).filter(Boolean)
    )
  );

  return (
    <Box
      as="main"
      boxShadow="base"
      mx={{ base: 0, sm: 4 }}
      h="100%"
      rounded="md"
      border="1px solid"
      borderColor="gray.200"
    >
      <Flex p={3} pb={0} align="flex-end" justify="space-between" flexWrap="wrap">
        <HStack align="flex-end" mr={5} mb={5}>
          <FormControl w="fit-content">
            <FormLabel textTransform="uppercase" fontSize="x-small" w="fit-content">
              Sort by
            </FormLabel>
            <Select
              minW="fit-content"
              size={isLargerThan567 ? "sm" : "xs"}
              rounded="base"
              borderColor="gray.500"
              cursor="pointer"
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
            >
              <option value="all">All Categories</option>
              {categories.map(category => (
                <option key={category} value={category}>
                  {category.charAt(0).toUpperCase() + category.slice(1)}
                </option>
              ))}
            </Select>
          </FormControl>
          <FormControl w="fit-content">
            <Select
              minW="fit-content"
              size={isLargerThan567 ? "sm" : "xs"}
              rounded="base"
              borderColor="gray.400"
              cursor="pointer"
              value={priceSort}
              onChange={(e) => setPriceSort(e.target.value)}
            >
              <option value="none">Sort by Price</option>
              <option value="low-to-high">Price: Low to High</option>
              <option value="high-to-low">Price: High to Low</option>
            </Select>
          </FormControl>
          <FormControl w="fit-content">
            <Select
              minW="fit-content"
              size={isLargerThan567 ? "sm" : "xs"}
              rounded="base"
              borderColor="gray.400"
              cursor="pointer"
              value={nameSort}
              onChange={(e) => setNameSort(e.target.value)}
            >
              <option value="none">Sort by Name</option>
              <option value="a-to-z">Name: A to Z</option>
              <option value="z-to-a">Name: Z to A</option>
            </Select>
          </FormControl>
        </HStack>
        <Flex align="center">
          <Tabs
            variant="unstyled"
            size="sm"
            mb={5}
            defaultIndex={
              location.pathname === "/"
                ? 0
                : location.pathname === "/saved"
                ? 1
                : undefined
            }
          >
            <TabList bg="appBlue.50" rounded="md">
              <Tab mediaQuery={isLargerThan567} navigatePath="/">
                Show All
              </Tab>
              <Tab mediaQuery={isLargerThan567} navigatePath="/saved">
                <MUIBadge badgeContent={savedItemsCount} testId="saved-count">Saved</MUIBadge>
              </Tab>
              <Tab mediaQuery={isLargerThan567} navigatePath="/cart">
                Buy now
              </Tab>
            </TabList>
          </Tabs>
        </Flex>
      </Flex>
      {children}
    </Box>
  );
};

export default Main;
