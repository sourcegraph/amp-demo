import {
  createContext,
  FC,
  ReactNode,
  useContext,
  useEffect,
  useState,
} from "react";

export type Currency = "USD" | "GBP" | "EUR" | "AUD" | "MXN" | "JPY";

export interface CurrencyInfo {
  code: Currency;
  symbol: string;
  name: string;
}

export const SUPPORTED_CURRENCIES: Record<Currency, CurrencyInfo> = {
  USD: { code: "USD", symbol: "$", name: "US Dollar" },
  GBP: { code: "GBP", symbol: "£", name: "British Pound" },
  EUR: { code: "EUR", symbol: "€", name: "Euro" },
  AUD: { code: "AUD", symbol: "A$", name: "Australian Dollar" },
  MXN: { code: "MXN", symbol: "MX$", name: "Mexican Peso" },
  JPY: { code: "JPY", symbol: "¥", name: "Japanese Yen" },
};

interface CurrencyContextType {
  currency: Currency;
  currencyInfo: CurrencyInfo;
  setCurrency: (currency: Currency) => void;
  formatPrice: (price: number | string) => string;
}

interface CurrencyProviderProps {
  children: ReactNode;
}

const CurrencyContext = createContext<CurrencyContextType | null>(null);

const CURRENCY_STORAGE_KEY = "preferred-currency";
const DEFAULT_CURRENCY: Currency = "USD";

export const CurrencyProvider: FC<CurrencyProviderProps> = ({ children }) => {
  const [currency, setCurrencyState] = useState<Currency>(() => {
    try {
      const saved = localStorage.getItem(CURRENCY_STORAGE_KEY);
      return (saved as Currency) || DEFAULT_CURRENCY;
    } catch (error) {
      console.error("Failed to load currency preference:", error);
      return DEFAULT_CURRENCY;
    }
  });

  const setCurrency = (newCurrency: Currency) => {
    setCurrencyState(newCurrency);
    try {
      localStorage.setItem(CURRENCY_STORAGE_KEY, newCurrency);
    } catch (error) {
      console.error("Failed to save currency preference:", error);
    }
  };

  const currencyInfo = SUPPORTED_CURRENCIES[currency];

  const formatPrice = (price: number | string): string => {
    const numPrice = typeof price === "string" ? parseFloat(price) : price;
    const { symbol } = currencyInfo;

    // For JPY, don't show decimal places
    if (currency === "JPY") {
      return `${symbol}${Math.round(numPrice).toLocaleString()}`;
    }

    return `${symbol}${numPrice.toFixed(2)}`;
  };

  useEffect(() => {
    // Validate stored currency on mount
    if (!Object.keys(SUPPORTED_CURRENCIES).includes(currency)) {
      setCurrency(DEFAULT_CURRENCY);
    }
  }, [currency]);

  return (
    <CurrencyContext.Provider
      value={{
        currency,
        currencyInfo,
        setCurrency,
        formatPrice,
      }}
    >
      {children}
    </CurrencyContext.Provider>
  );
};

export const useCurrency = (): CurrencyContextType => {
  const context = useContext(CurrencyContext);
  if (!context) {
    throw new Error("useCurrency must be used within a CurrencyProvider");
  }
  return context;
};
