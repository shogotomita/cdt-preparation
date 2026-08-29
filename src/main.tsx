import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { HashRouter, Route, Routes } from 'react-router-dom'
import { AppProvider } from './context/AppContext'
import './index.css'
import { HomePage } from './pages/HomePage'
import { QuizPage } from './pages/QuizPage'
import { ResultPage } from './pages/ResultPage'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <HashRouter>
      <AppProvider>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/quiz/:yearId/:subjectId" element={<QuizPage />} />
          <Route path="/result/:yearId/:subjectId" element={<ResultPage />} />
        </Routes>
      </AppProvider>
    </HashRouter>
  </StrictMode>,
)
