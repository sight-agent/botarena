import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import App from './App'

test('renders app shell', () => {
  render(
    <MemoryRouter initialEntries={['/env/ipd']}>
      <App />
    </MemoryRouter>
  )
  expect(screen.getByText('botarena')).toBeInTheDocument()
  expect(screen.getByText(/Iterated Prisoner/i)).toBeInTheDocument()
})

