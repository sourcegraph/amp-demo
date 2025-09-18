import { ChevronDownIcon } from "@chakra-ui/icons";
import {
  Box,
  Button,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  Text,
  HStack,
} from "@chakra-ui/react";
import {
  useCurrency,
  SUPPORTED_CURRENCIES,
  Currency,
} from "../context/CurrencyContext";

interface CurrencySelectorProps {
  size?: "sm" | "md" | "lg";
  variant?: "outline" | "ghost" | "solid";
}

const CurrencySelector = ({
  size = "sm",
  variant = "ghost",
}: CurrencySelectorProps) => {
  const { currency, setCurrency, currencyInfo } = useCurrency();

  return (
    <Menu>
      <MenuButton
        as={Button}
        rightIcon={<ChevronDownIcon />}
        variant={variant}
        size={size}
        fontWeight="normal"
        color="gray.600"
        _hover={{
          bg: "gray.50",
          color: "appBlue.400",
        }}
        _active={{
          bg: "gray.100",
          color: "appBlue.500",
        }}
      >
        <HStack spacing={1}>
          <Text fontSize={size === "sm" ? "sm" : "md"}>
            {currencyInfo.symbol}
          </Text>
          <Text fontSize={size === "sm" ? "xs" : "sm"}>
            {currencyInfo.code}
          </Text>
        </HStack>
      </MenuButton>
      <MenuList>
        {Object.values(SUPPORTED_CURRENCIES).map((currencyOption) => (
          <MenuItem
            key={currencyOption.code}
            onClick={() => setCurrency(currencyOption.code as Currency)}
            bg={currency === currencyOption.code ? "blue.50" : "transparent"}
            color={
              currency === currencyOption.code ? "appBlue.500" : "gray.700"
            }
            _hover={{
              bg: currency === currencyOption.code ? "blue.100" : "gray.50",
            }}
          >
            <HStack spacing={3} w="full">
              <Text
                fontWeight={
                  currency === currencyOption.code ? "semibold" : "normal"
                }
              >
                {currencyOption.symbol}
              </Text>
              <Box>
                <Text
                  fontSize="sm"
                  fontWeight={
                    currency === currencyOption.code ? "semibold" : "normal"
                  }
                >
                  {currencyOption.code}
                </Text>
                <Text fontSize="xs" color="gray.500">
                  {currencyOption.name}
                </Text>
              </Box>
            </HStack>
          </MenuItem>
        ))}
      </MenuList>
    </Menu>
  );
};

export default CurrencySelector;
