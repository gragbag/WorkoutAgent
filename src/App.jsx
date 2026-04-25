import { useEffect, useState } from 'react'
import PlannerDashboard from './PlannerDashboard.jsx'
import { isSupabaseConfigured, supabase } from './lib/supabase.js'

const authInputClass =
  'w-full rounded-[18px] border border-white/12 bg-white/[0.04] px-4 py-3.5 text-[#f5efe4] outline-none transition focus:border-[#ffb37c]/50 focus:ring-2 focus:ring-[#f08f56]/20'

function App() {
  const [session, setSession] = useState(null)
  const [mode, setMode] = useState('signin')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [authMessage, setAuthMessage] = useState('')
  const [authError, setAuthError] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    if (!supabase) {
      setIsLoading(false)
      return
    }

    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session ?? null)
      setIsLoading(false)
    })

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      setSession(nextSession)
      setIsLoading(false)
    })

    return () => subscription.unsubscribe()
  }, [])

  async function handleAuthSubmit(event) {
    event.preventDefault()
    setAuthError('')
    setAuthMessage('')

    if (!supabase) {
      setAuthError('Supabase is not configured yet.')
      return
    }

    if (mode === 'signup' && password !== confirmPassword) {
      setAuthError('Passwords do not match.')
      return
    }

    setIsSubmitting(true)

    try {
      if (mode === 'signup') {
        const { error } = await supabase.auth.signUp({
          email,
          password,
        })

        if (error) {
          throw error
        }

        setAuthMessage('Account created. If email confirmation is enabled, check your inbox.')
      } else {
        const { error } = await supabase.auth.signInWithPassword({
          email,
          password,
        })

        if (error) {
          throw error
        }

        setAuthMessage('Signed in successfully.')
      }
    } catch (error) {
      setAuthError(error instanceof Error ? error.message : 'Authentication failed.')
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handleSignOut() {
    if (!supabase) {
      return
    }

    await supabase.auth.signOut()
    setAuthMessage('')
    setAuthError('')
  }

  if (isLoading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[#0e1113] px-4 text-[#f5efe4]">
        <div className="rounded-[24px] border border-white/10 bg-white/[0.03] px-6 py-5 text-sm">
          Loading authentication...
        </div>
      </main>
    )
  }

  if (!isSupabaseConfigured) {
    return (
      <main className="min-h-screen bg-[radial-gradient(circle_at_top_left,rgba(240,119,64,0.22),transparent_28%),radial-gradient(circle_at_85%_20%,rgba(91,149,117,0.18),transparent_22%),linear-gradient(160deg,#201714_0%,#0e1113_52%,#12181a_100%)] px-4 py-8 text-[#f5efe4]">
        <section className="mx-auto max-w-3xl rounded-[32px] border border-white/10 bg-[rgba(15,19,21,0.74)] p-8 shadow-[0_24px_90px_rgba(0,0,0,0.24)]">
          <p className="text-[0.72rem] uppercase tracking-[0.14em] text-[#c2b7a6]">
            Supabase setup required
          </p>
          <h1 className="mt-3 text-4xl leading-tight font-semibold tracking-[-0.04em] text-[#f9f2e8]">
            Add your Supabase project keys to enable sign up and login.
          </h1>
          <p className="mt-5 text-base leading-7 text-[#efe7d8]">
            Create a Supabase project, turn on email/password auth, and set the two Vite
            environment variables below in your local `.env`.
          </p>
          <pre className="mt-6 overflow-x-auto rounded-[22px] border border-white/10 bg-black/20 p-5 text-sm leading-6 text-[#efe7d8]">
{`VITE_SUPABASE_URL=your-project-url
VITE_SUPABASE_PUBLISHABLE_KEY=your-publishable-key`}
          </pre>
        </section>
      </main>
    )
  }

  if (session?.user) {
    return (
      <PlannerDashboard
        userId={session.user.id}
        userEmail={session.user.email ?? 'Signed-in user'}
        onSignOut={handleSignOut}
      />
    )
  }

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top_left,rgba(240,119,64,0.22),transparent_28%),radial-gradient(circle_at_85%_20%,rgba(91,149,117,0.18),transparent_22%),linear-gradient(160deg,#201714_0%,#0e1113_52%,#12181a_100%)] px-4 py-8 text-[#f5efe4]">
      <section className="mx-auto grid max-w-6xl gap-6 lg:grid-cols-[1.15fr_0.85fr]">
        <article className="rounded-[32px] border border-white/10 bg-[rgba(15,19,21,0.74)] p-8 shadow-[0_24px_90px_rgba(0,0,0,0.24)]">
          <p className="text-[0.72rem] uppercase tracking-[0.14em] text-[#c2b7a6]">
            WorkoutAgent access
          </p>
          <h1 className="mt-3 max-w-[11ch] text-[clamp(2.8rem,7vw,5.4rem)] leading-[0.95] font-semibold tracking-[-0.05em] text-[#f9f2e8]">
            Sign in before you generate plans.
          </h1>
          <p className="mt-5 max-w-2xl text-base leading-7 text-[#efe7d8]">
            Add a real user layer to the project so you can support saved plans, user
            history, protected generation, and future personalization work.
          </p>
        </article>

        <section className="rounded-[28px] border border-white/10 bg-[rgba(15,19,21,0.74)] p-6 shadow-[0_24px_90px_rgba(0,0,0,0.24)]">
          <div className="mb-6 flex gap-2 rounded-full border border-white/10 bg-white/[0.03] p-1">
            <button
              type="button"
              onClick={() => setMode('signin')}
              className={`flex-1 rounded-full px-4 py-2.5 text-sm font-medium transition ${
                mode === 'signin'
                  ? 'bg-[linear-gradient(135deg,#f08f56,#da5d3d)] text-[#111]'
                  : 'text-[#efe7d8]'
              }`}
            >
              Sign in
            </button>
            <button
              type="button"
              onClick={() => setMode('signup')}
              className={`flex-1 rounded-full px-4 py-2.5 text-sm font-medium transition ${
                mode === 'signup'
                  ? 'bg-[linear-gradient(135deg,#f08f56,#da5d3d)] text-[#111]'
                  : 'text-[#efe7d8]'
              }`}
            >
              Sign up
            </button>
          </div>

          <form className="grid gap-4" onSubmit={handleAuthSubmit}>
            <div className="grid gap-2">
              <label className="text-[0.72rem] uppercase tracking-[0.14em] text-[#c2b7a6]" htmlFor="email">
                Email
              </label>
              <input
                id="email"
                type="email"
                className={authInputClass}
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                required
              />
            </div>

            <div className="grid gap-2">
              <label className="text-[0.72rem] uppercase tracking-[0.14em] text-[#c2b7a6]" htmlFor="password">
                Password
              </label>
              <input
                id="password"
                type="password"
                className={authInputClass}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
              />
            </div>

            {mode === 'signup' ? (
              <div className="grid gap-2">
                <label
                  className="text-[0.72rem] uppercase tracking-[0.14em] text-[#c2b7a6]"
                  htmlFor="confirm-password"
                >
                  Confirm password
                </label>
                <input
                  id="confirm-password"
                  type="password"
                  className={authInputClass}
                  value={confirmPassword}
                  onChange={(event) => setConfirmPassword(event.target.value)}
                  required
                />
              </div>
            ) : null}

            {authError ? (
              <div className="rounded-[18px] border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
                {authError}
              </div>
            ) : null}

            {authMessage ? (
              <div className="rounded-[18px] border border-emerald-400/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-100">
                {authMessage}
              </div>
            ) : null}

            <button
              type="submit"
              disabled={isSubmitting}
              className="mt-2 rounded-full bg-[linear-gradient(135deg,#f08f56,#da5d3d)] px-4 py-3 font-semibold text-[#111] transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0"
            >
              {isSubmitting
                ? 'Working...'
                : mode === 'signup'
                  ? 'Create account'
                  : 'Sign in'}
            </button>
          </form>

          <p className="mt-5 text-sm leading-6 text-[#c2b7a6]">
            Supabase handles the user identity layer here. The planner stays in your app
            once a session exists.
          </p>
        </section>
      </section>
    </main>
  )
}

export default App
