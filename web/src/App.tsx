import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { IssuePage } from './pages/issue/IssuePage'
import { IssuesPage } from './pages/IssuesPage'
import { MetricsPage } from './pages/MetricsPage'
import { NewIssuePage } from './pages/new/NewIssuePage'
import { PlatformPage } from './pages/PlatformPage'
import { TemplatesPage } from './pages/TemplatesPage'

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<NewIssuePage />} />
          <Route path="issues" element={<IssuesPage />} />
          <Route path="issues/:id" element={<IssuePage />} />
          <Route path="templates" element={<TemplatesPage />} />
          <Route path="metrics" element={<MetricsPage />} />
          <Route path="platform" element={<PlatformPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
