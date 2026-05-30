import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ErrorBoundary, ToastProvider } from '@njz-os/ui';
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
import { AuthProvider } from './auth/AuthProvider';
import { SignInRoute } from './auth/SignInRoute';
import { AccountRoute } from './auth/AccountRoute';
import { OnboardingRoute } from './onboarding/OnboardingRoute';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 30_000, retry: 1 },
  },
});

function wrap(moduleSlug: string, moduleLabel: string, element: React.ReactElement) {
  return (
    <ErrorBoundary moduleSlug={moduleSlug} moduleLabel={moduleLabel}>
      {element}
    </ErrorBoundary>
  );
}

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <AuthProvider>
          <BrowserRouter>
            <Routes>
              <Route path="/" element={<ShellLayout />}>
                <Route index element={wrap('home', 'Home', <HomeRoute />)} />
                <Route path="focus/*" element={wrap('focus-hero', 'Focus Hero', <FocusRoute />)} />
                <Route path="sound/*" element={wrap('soundscapes', 'Soundscapes', <SoundRoute />)} />
                <Route path="blocker/*" element={wrap('distraction-blocker', 'Distraction Blocker', <BlockerRoute />)} />
                <Route path="write/*" element={wrap('writing-space', 'Writing Space', <WriteRoute />)} />
                <Route path="learn/*" element={wrap('micro-learning', 'Micro-Learning', <LearnRoute />)} />
                <Route path="train/*" element={wrap('brain-training', 'Brain Training', <TrainRoute />)} />
                <Route path="world/*" element={wrap('polyco-world', 'PolyCo.World', <WorldRoute />)} />
                <Route path="sign-in" element={wrap('sign-in', 'Sign in', <SignInRoute />)} />
                <Route path="account" element={wrap('account', 'Account', <AccountRoute />)} />
                <Route path="onboarding" element={wrap('onboarding', 'Onboarding', <OnboardingRoute />)} />
                <Route path="*" element={<NotFoundRoute />} />
              </Route>
            </Routes>
          </BrowserRouter>
        </AuthProvider>
      </ToastProvider>
    </QueryClientProvider>
  );
}

export { Link };
