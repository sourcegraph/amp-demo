import React from 'react'
import { reportError } from './errorReporter'
import { Box, Button, Heading, Text, VStack } from '@chakra-ui/react'

interface Props {
  readonly children: React.ReactNode
}

interface State {
  readonly hasError: boolean
  readonly requestId?: string
}

export class ErrorBoundary extends React.Component<Props, State> {
  state: State = { hasError: false }

  static getDerivedStateFromError(): State {
    return { hasError: true }
  }

  componentDidCatch(error: Error, info: React.ErrorInfo): void {
    reportError({
      error,
      info,
      context: { location: window.location.href },
    })
  }

  handleReload = (): void => {
    window.location.reload()
  }

  handleGoHome = (): void => {
    window.location.href = '/'
  }

  render(): React.ReactNode {
    if (this.state.hasError) {
      return (
        <Box
          minH="100vh"
          display="flex"
          alignItems="center"
          justifyContent="center"
          bg="sand.50"
        >
          <VStack spacing={6} maxW="md" textAlign="center" p={8}>
            <Heading size="xl" color="ink.900">
              Something went wrong
            </Heading>
            <Text color="ink.700">
              An unexpected error occurred. Please try reloading the page or return to the home
              page.
            </Text>
            <VStack spacing={3} w="full">
              <Button colorScheme="blue" onClick={this.handleReload} w="full">
                Reload Page
              </Button>
              <Button variant="outline" onClick={this.handleGoHome} w="full">
                Go to Home
              </Button>
            </VStack>
          </VStack>
        </Box>
      )
    }
    return this.props.children
  }
}
