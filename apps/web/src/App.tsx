import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ShellLayout } from './shell/ShellLayout';
import { HomeRoute } from './routes/HomeRoute';
import { FocusRoute } from './modules/focus-hero/FocusRoute';
import { SoundRoute } from './modules/soundscapes/SoundRoute';
import { BlockerRoute } from './modules/distraction-blocker/BlockerRoute';
import { WriteRoute } from './modules/writing-space/WriteRoute';
import { LearnRoute } from './modules/micro-learning/LearnRoute';
import { TrainRoute } from './modules/brain-training/TrainRoute';
import { WorldRoute } from './modules/polyco-world/WorldRoute';
import { NotFoundRoute } from './routes/NotFoundRoute';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 30_000, retry: 1 },
  },
});

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<ShellLayout />}>
            <Route index element={<HomeRoute />} />
            <Route path="focus/*" element={<FocusRoute />} />
            <Route path="sound/*" element={<SoundRoute />} />
            <Route path="blocker/*" element={<BlockerRoute />} />
            <Route path="write/*" element={<WriteRoute />} />
            <Route path="learn/*" element={<LearnRoute />} />
            <Route path="train/*" element={<TrainRoute />} />
            <Route path="world/*" element={<WorldRoute />} />
            <Route path="*" element={<NotFoundRoute />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export { Link };
