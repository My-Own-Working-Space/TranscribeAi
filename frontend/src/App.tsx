import React, { useState, useEffect, useRef, createContext, useContext } from 'react';
import { jobsApi, aiApi, feedbackApi } from './services/api';
import { supabase } from './services/supabase';
import { t } from './i18n';
import {
  CheckCircle2, Loader2, Sparkles, AlertTriangle,
  FileText, Info, Mic, Clock, Zap, Globe, Share2,
  LogOut, LayoutDashboard, Plus, Trash2, MessageSquare, ListChecks,
  Send, RefreshCw, ArrowLeft, Languages, Heart, Mail,
  PanelRightClose, PanelRightOpen, Copy, ChevronDown, ChevronUp,
  User, CreditCard, Crown, Shield, MessageCircle, Sun, Moon,
  ServerCrash, SearchX, WifiOff, Home,
} from 'lucide-react';

const LangContext = createContext<{ lang: string; toggle: () => void }>({ lang: 'vi', toggle: () => { } });
const useLang = () => useContext(LangContext);

const ThemeContext = createContext<{ theme: string; toggleTheme: () => void }>({ theme: 'light', toggleTheme: () => { } });
const useTheme = () => useContext(ThemeContext);


interface UserData {
  id: string; email: string; full_name: string; plan: string;
  monthly_minutes_used: number; monthly_minutes_limit: number;
}

interface AuthCtx {
  user: UserData | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthCtx>(null!);
const useAuth = () => useContext(AuthContext);

function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserData | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchProfile = async (userId: string, email: string) => {
    const { data } = await supabase.from('profiles').select('*').eq('id', userId).single();
    if (data) {
      setUser({ id: data.id, email: data.email || email, full_name: data.full_name || '', plan: data.plan || 'free', monthly_minutes_used: data.monthly_minutes_used || 0, monthly_minutes_limit: data.monthly_minutes_limit || 9999 });
    } else {
      setUser({ id: userId, email, full_name: '', plan: 'free', monthly_minutes_used: 0, monthly_minutes_limit: 9999 });
    }
  };

  useEffect(() => {
    supabase.auth.getSession().then(async ({ data: { session } }) => {
      if (session?.user) {
        try {
          await fetchProfile(session.user.id, session.user.email || '');
        } catch (e) {
          console.error('fetchProfile failed:', e);
        }
      }
      setLoading(false);
    }).catch((err) => {
      console.error('getSession failed:', err);
      setLoading(false);
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      if (session?.user) {
        fetchProfile(session.user.id, session.user.email || '');
      } else {
        setUser(null);
      }
    });

    return () => subscription.unsubscribe();
  }, []);

  const login = async (email: string, password: string) => {
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) throw new Error(error.message);
  };

  const register = async (email: string, password: string, name: string) => {
    const { error } = await supabase.auth.signUp({
      email, password,
      options: { data: { full_name: name } }
    });
    if (error) throw new Error(error.message);
  };

  const logout = () => { supabase.auth.signOut(); setUser(null); };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}


interface ToastMsg { id: string; message: string; type: 'success' | 'info' | 'error'; }
let _showToast: (msg: string, type: 'success' | 'info' | 'error') => void = () => {};

function ToastContainer() {
  const [toasts, setToasts] = useState<ToastMsg[]>([]);
  useEffect(() => {
    _showToast = (message, type) => {
      const id = Math.random().toString(36).slice(2, 9);
      setToasts(p => [...p, { id, message, type }]);
      setTimeout(() => setToasts(p => p.filter(t => t.id !== id)), 4000);
    };
  }, []);
  return (
    <div className="toast-container">
      {toasts.map(t => (
        <div key={t.id} className="toast">
          {t.type === 'success' && <CheckCircle2 className="w-5 h-5 text-emerald-400" />}
          {t.type === 'error' && <AlertTriangle className="w-5 h-5 text-red-500" />}
          {t.type === 'info' && <Info className="w-5 h-5 text-accent" />}
          <span className="text-sm font-medium">{t.message}</span>
        </div>
      ))}
    </div>
  );
}

const toast = (m: string, t: 'success' | 'info' | 'error' = 'info') => _showToast?.(m, t);


/* ── Error Pages ─────────────────────────────────────────────────── */

function NotFoundPage({ navigate }: { navigate: (to: string) => void }) {
  const { lang } = useLang();
  return (
    <section className="error-page">
      <div className="error-page-content">
        <SearchX className="error-page-icon" />
        <h1 className="error-page-code">404</h1>
        <h2 className="error-page-title">{t('err_404_title', lang)}</h2>
        <p className="error-page-desc">{t('err_404_desc', lang)}</p>
        <button className="btn-primary" onClick={() => navigate('/')}>
          <Home className="w-4 h-4" /> {t('err_go_home', lang)}
        </button>
      </div>
    </section>
  );
}

function ServerErrorPage({ navigate, code = 500 }: { navigate: (to: string) => void; code?: number }) {
  const { lang } = useLang();
  return (
    <section className="error-page">
      <div className="error-page-content">
        <ServerCrash className="error-page-icon" />
        <h1 className="error-page-code">{code}</h1>
        <h2 className="error-page-title">{t('err_500_title', lang)}</h2>
        <p className="error-page-desc">{t('err_500_desc', lang)}</p>
        <div className="error-page-actions">
          <button className="btn-primary" onClick={() => window.location.reload()}>
            <RefreshCw className="w-4 h-4" /> {t('err_retry', lang)}
          </button>
          <button className="btn-ghost" onClick={() => navigate('/')}>
            <Home className="w-4 h-4" /> {t('err_go_home', lang)}
          </button>
        </div>
      </div>
    </section>
  );
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
function NetworkErrorPage({ navigate: _nav }: { navigate: (to: string) => void }) {
  const { lang } = useLang();
  return (
    <section className="error-page">
      <div className="error-page-content">
        <WifiOff className="error-page-icon" />
        <h1 className="error-page-code">!</h1>
        <h2 className="error-page-title">{t('err_network_title', lang)}</h2>
        <p className="error-page-desc">{t('err_network_desc', lang)}</p>
        <button className="btn-primary" onClick={() => window.location.reload()}>
          <RefreshCw className="w-4 h-4" /> {t('err_retry', lang)}
        </button>
      </div>
    </section>
  );
}

class ErrorBoundary extends React.Component<
  { children: React.ReactNode; navigate: (to: string) => void },
  { hasError: boolean; error: Error | null }
> {
  constructor(props: { children: React.ReactNode; navigate: (to: string) => void }) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }
  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error('[ErrorBoundary]', error, info.componentStack);
  }
  render() {
    if (this.state.hasError) {
      return <ServerErrorPage navigate={this.props.navigate} code={500} />;
    }
    return this.props.children;
  }
}


function useRouter() {
  const [path, setPath] = useState(window.location.pathname);
  useEffect(() => {
    const onPop = () => setPath(window.location.pathname);
    window.addEventListener('popstate', onPop);
    return () => window.removeEventListener('popstate', onPop);
  }, []);
  const navigate = (to: string) => { window.history.pushState({}, '', to); setPath(to); };
  return { path, navigate };
}


function Navbar({ navigate }: { navigate: (to: string) => void }) {
  const { user, logout } = useAuth();
  const { lang, toggle } = useLang();
  const { theme, toggleTheme } = useTheme();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) setMenuOpen(false);
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const go = (to: string) => { setMenuOpen(false); navigate(to); };

  return (
    <nav>
      <div className="nav-logo" onClick={() => navigate(user ? '/dashboard' : '/')}>
        <div className="logo-icon">
          <span style={{ color: 'var(--btn-primary-text)', fontWeight: 800, fontSize: '15px', lineHeight: 1 }}>T</span>
        </div>
        TranscribeAI
      </div>
      {user ? (
        <div className="nav-right" style={{ gap: '8px', alignItems: 'center' }}>
          <div className="plan-badge">
            <Sparkles className="w-3 h-3" />
            {user.plan.toUpperCase()} · {user.monthly_minutes_limit >= 9999 ? t('nav_unlimited', lang) : `${user.monthly_minutes_used}/${user.monthly_minutes_limit} ${t('nav_minutes', lang)}`}
          </div>
          <button className="btn-ghost" onClick={() => navigate('/dashboard')}>
            <LayoutDashboard className="w-4 h-4" /> {t('nav_dashboard', lang)}
          </button>
          <button className="btn-ghost" onClick={() => navigate('/studio')}>
            <Plus className="w-4 h-4" /> {t('nav_new', lang)}
          </button>
          <div className="nav-menu-wrapper" ref={menuRef}>
            <button className="btn-ghost" onClick={() => setMenuOpen(!menuOpen)}>
              <User className="w-4 h-4" />
              <ChevronDown className="w-3 h-3" style={{ marginLeft: '-4px', opacity: 0.5 }} />
            </button>
            {menuOpen && (
              <div className="nav-dropdown">
                <div className="nav-dropdown-header">
                  <p style={{ fontWeight: 600, fontSize: '14px' }}>{user.full_name || user.email}</p>
                  <p style={{ fontSize: '12px', color: 'var(--muted)' }}>{user.email}</p>
                </div>
                <div className="nav-dropdown-divider" />
                <button className="nav-dropdown-item" onClick={() => go('/profile')}>
                  <User className="w-4 h-4" /> {t('nav_profile', lang)}
                </button>
                <button className="nav-dropdown-item" onClick={() => go('/pricing')}>
                  <CreditCard className="w-4 h-4" /> {t('nav_pricing', lang)}
                </button>
                <button className="nav-dropdown-item" onClick={() => go('/feedback')}>
                  <MessageCircle className="w-4 h-4" /> {t('nav_feedback', lang)}
                </button>
                <div className="nav-dropdown-divider" />
                <button className="nav-dropdown-item" onClick={() => { setMenuOpen(false); toggleTheme(); }}>
                  {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
                  {theme === 'dark' ? 'Light mode' : 'Dark mode'}
                </button>
                <button className="nav-dropdown-item" onClick={() => { setMenuOpen(false); toggle(); }}>
                  <Languages className="w-4 h-4" /> {lang === 'vi' ? 'English' : 'Tiếng Việt'}
                </button>
                <div className="nav-dropdown-divider" />
                <button className="nav-dropdown-item nav-dropdown-danger" onClick={() => { setMenuOpen(false); logout(); navigate('/'); }}>
                  <LogOut className="w-4 h-4" /> {t('nav_signout', lang)}
                </button>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="nav-right" style={{ gap: '8px', alignItems: 'center' }}>
          <button className="btn-ghost" onClick={() => navigate('/pricing')}>
            {t('nav_pricing', lang)}
          </button>
          <button className="btn-ghost" onClick={() => navigate('/feedback')}>
            <MessageCircle className="w-4 h-4" /> {t('nav_feedback', lang)}
          </button>
          <button className="btn-ghost" onClick={toggleTheme}>
            {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </button>
          <button className="btn-ghost" onClick={toggle}>
            <Languages className="w-4 h-4" /> {lang === 'vi' ? 'EN' : 'VI'}
          </button>
          <button className="btn-ghost" onClick={() => navigate('/login')}>{t('nav_signin', lang)}</button>
          <button className="btn-primary" onClick={() => navigate('/register')}>{t('nav_start_free', lang)}</button>
        </div>
      )}
    </nav>
  );
}


function LoginPage({ navigate }: { navigate: (to: string) => void }) {
  const { login } = useAuth();
  const { lang } = useLang();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [remember, setRemember] = useState(true);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(email, password);
      navigate('/dashboard');
      toast(t('login_success', lang), 'success');
    } catch (err: unknown) {
      toast((err instanceof Error ? err.message : null) || t('login_fail', lang), 'error');
    } finally { setLoading(false); }
  };

  return (
    <section className="auth-section">
      <div className="auth-card">
        <h2>{t('login_title', lang)}</h2>
        <p className="text-muted" style={{ marginBottom: '24px' }}>{t('login_subtitle', lang)}</p>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>{t('login_email', lang)}</label>
            <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@example.com" required />
          </div>
          <div className="form-group">
            <label>{t('login_password', lang)}</label>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="••••••••" required />
          </div>
          <div className="remember-row">
            <label className="remember-label">
              <input type="checkbox" checked={remember} onChange={e => setRemember(e.target.checked)} />
              {t('login_remember', lang)}
            </label>
            <button type="button" className="forgot-link" onClick={() => toast(t('login_forgot_toast', lang), 'info')}>{t('login_forgot', lang)}</button>
          </div>
          <button type="submit" className="btn-primary" disabled={loading} style={{ width: '100%', padding: '14px' }}>
            {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : t('login_button', lang)}
          </button>
        </form>
        <p className="auth-switch">
          {t('login_no_account', lang)} <span onClick={() => navigate('/register')}>{t('login_register_link', lang)}</span>
        </p>
      </div>
    </section>
  );
}


function RegisterPage({ navigate }: { navigate: (to: string) => void }) {
  const { register } = useAuth();
  const { lang } = useLang();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [registered, setRegistered] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password.length < 6) { toast(t('register_pw_short', lang), 'error'); return; }
    setLoading(true);
    try {
      await register(email, password, name);
      setRegistered(true);
    } catch (err: unknown) {
      toast((err instanceof Error ? err.message : null) || t('register_fail', lang), 'error');
    } finally { setLoading(false); }
  };

  if (registered) {
    return (
      <section className="auth-section">
        <div className="auth-card" style={{ textAlign: 'center' }}>
          <div className="verify-email-icon">
            <Mail className="w-12 h-12" />
          </div>
          <h2 style={{ marginBottom: '12px' }}>{t('verify_title', lang)}</h2>
          <p className="text-muted" style={{ marginBottom: '8px', lineHeight: 1.7 }}>
            {t('verify_sent', lang)}
          </p>
          <p style={{ color: 'var(--accent)', fontWeight: 600, fontSize: '16px', marginBottom: '20px' }}>{email}</p>
          <div className="verify-email-tips">
            <div className="verify-tip">
              <Info className="w-4 h-4" />
              <span>{t('verify_spam', lang)} <strong>{t('verify_spam_bold', lang)}</strong> {t('verify_spam_suffix', lang)}</span>
            </div>
            <div className="verify-tip">
              <Clock className="w-4 h-4" />
              <span>{t('verify_wait', lang)}</span>
            </div>
            <div className="verify-tip">
              <CheckCircle2 className="w-4 h-4" />
              <span>{t('verify_click', lang)}</span>
            </div>
          </div>
          <button className="btn-primary" onClick={() => navigate('/login')} style={{ width: '100%', padding: '14px', marginTop: '24px' }}>
            {t('verify_done', lang)}
          </button>
          <p className="text-muted" style={{ marginTop: '16px', fontSize: '13px' }}>
            {t('verify_no_email', lang)} <span style={{ color: 'var(--accent)', cursor: 'pointer' }} onClick={() => { setRegistered(false); toast(t('verify_retry_toast', lang), 'info'); }}>{t('verify_retry', lang)}</span>
          </p>
        </div>
      </section>
    );
  }

  return (
    <section className="auth-section">
      <div className="auth-card">
        <h2>{t('register_title', lang)}</h2>
        <p className="text-muted" style={{ marginBottom: '24px' }}>{t('register_subtitle', lang)}</p>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>{t('register_name', lang)}</label>
            <input type="text" value={name} onChange={e => setName(e.target.value)} placeholder={lang === 'vi' ? 'Nguyễn Văn A' : 'John Doe'} />
          </div>
          <div className="form-group">
            <label>{t('login_email', lang)}</label>
            <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@example.com" required />
          </div>
          <div className="form-group">
            <label>{t('login_password', lang)}</label>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder={t('register_password_hint', lang)} required />
          </div>
          <div className="remember-row" style={{ justifyContent: 'flex-start' }}>
            <label className="remember-label">
              <input type="checkbox" defaultChecked />
              {t('register_agree', lang)} <span style={{ color: 'var(--accent)', cursor: 'pointer' }}>{t('register_terms', lang)}</span>
            </label>
          </div>
          <button type="submit" className="btn-primary" disabled={loading} style={{ width: '100%', padding: '14px' }}>
            {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : t('register_button', lang)}
          </button>
        </form>
        <p className="auth-switch">
          {t('register_has_account', lang)} <span onClick={() => navigate('/login')}>{t('register_login_link', lang)}</span>
        </p>
      </div>
    </section>
  );
}


function DashboardPage({ navigate }: { navigate: (to: string) => void }) {
  const { user } = useAuth();
  const { lang } = useLang();
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [jobs, setJobs] = useState<any[]>([]);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([jobsApi.list(), jobsApi.dashboard()])
      .then(([j, s]) => { setJobs(j.data); setStats(s.data); })
      .catch(() => toast(t('dash_load_fail', lang), 'error'))
      .finally(() => setLoading(false));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const deleteJob = async (id: string) => {
    try {
      await jobsApi.delete(id);
      setJobs(j => j.filter(x => x.id !== id));
      toast(t('dash_deleted', lang), 'success');
    } catch { toast(t('dash_delete_fail', lang), 'error'); }
  };

  if (loading) return <div className="page-loader"><Loader2 className="w-10 h-10 animate-spin text-accent" /></div>;

  return (
    <section className="dashboard-section">
      <div className="dashboard-header" style={{ marginBottom: '40px' }}>
        <h1 style={{ fontSize: '32px', marginBottom: '8px' }}>{t('dash_greeting', lang)} {user?.full_name?.split(' ')[0] || (lang === 'vi' ? 'bạn' : 'there')}{t('dash_greeting_suffix', lang)}</h1>
        <p className="text-muted">{t('dash_subtitle', lang)}</p>
      </div>

      <div className="studio-cta-card" onClick={() => navigate('/studio')} style={{
        background: 'rgba(126, 179, 255, 0.05)',
        border: '1px solid rgba(126, 179, 255, 0.2)',
        borderRadius: '24px',
        padding: '32px',
        marginBottom: '40px',
        cursor: 'pointer',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        transition: 'all 0.3s ease'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
          <div style={{ width: '64px', height: '64px', borderRadius: '16px', background: 'var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Plus className="w-8 h-8 text-white" />
          </div>
          <div>
            <h2 style={{ fontSize: '20px', marginBottom: '4px' }}>{t('dash_new_session', lang)}</h2>
            <p className="text-muted">{t('dash_new_session_desc', lang)}</p>
          </div>
        </div>
        <div className="btn-primary" style={{ padding: '12px 24px' }}>{t('dash_open_studio', lang)}</div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-card-icon"><FileText className="w-5 h-5" /></div>
            <div className="stat-card-value">{stats.total_jobs}</div>
            <div className="stat-card-label">{t('dash_stat_saved', lang)}</div>
          </div>
          <div className="stat-card">
            <div className="stat-card-icon"><MessageSquare className="w-5 h-5" /></div>
            <div className="stat-card-value">{stats.completed_jobs}</div>
            <div className="stat-card-label">{t('dash_stat_ai', lang)}</div>
          </div>
          <div className="stat-card">
            <div className="stat-card-icon"><Clock className="w-5 h-5" /></div>
            <div className="stat-card-value">{stats.total_minutes_transcribed}</div>
            <div className="stat-card-label">{t('dash_stat_minutes', lang)}</div>
          </div>
          <div className="stat-card">
            <div className="stat-card-icon"><Zap className="w-5 h-5" /></div>
            <div className="stat-card-value">{t('dash_stat_trial', lang)}</div>
            <div className="stat-card-label">{t('dash_stat_trial_label', lang)}</div>
          </div>
        </div>
      )}

      {/* Jobs List */}
      <div className="jobs-list">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h3>{t('dash_recent', lang)}</h3>
          <span style={{ fontSize: '13px', color: 'var(--accent)', cursor: 'pointer' }}>{t('dash_view_all', lang)}</span>
        </div>

        {jobs.length === 0 ? (
          <div className="empty-state">
            <Mic className="w-12 h-12 text-muted" style={{ opacity: 0.3 }} />
            <p>{t('dash_empty', lang)}</p>
          </div>
        ) : (
          <div style={{ display: 'grid', gap: '12px' }}>
            {jobs.map(job => (
              <div key={job.id} className="job-card" onClick={() => navigate(`/results/${job.id}`)}>
                <div className="job-card-left">
                  <div className={`job-status-dot ${job.status}`} />
                  <div>
                    <div className="job-filename">{job.original_filename || 'Untitled'}</div>
                    <div className="job-meta">
                      {job.mode} · {new Date(job.created_at).toLocaleDateString(lang === 'vi' ? 'vi-VN' : 'en-US')}
                    </div>
                  </div>
                </div>
                <div className="job-card-right">
                  {job.has_summary && <span className="badge-ai" style={{ fontSize: '11px' }}>AI READY</span>}
                  <button className="btn-ghost" style={{ padding: '6px 12px', fontSize: '12px' }}>{t('dash_view_result', lang)}</button>
                  <button className="icon-btn" onClick={(e) => { e.stopPropagation(); deleteJob(job.id); }}>
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}


function ProfilePage({ navigate }: { navigate: (to: string) => void }) {
  const { user } = useAuth();
  const { lang } = useLang();
  const [name, setName] = useState(user?.full_name || '');
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    if (!user) return;
    setSaving(true);
    try {
      const { error } = await supabase.from('profiles').update({ full_name: name }).eq('id', user.id);
      if (error) throw error;
      toast(lang === 'vi' ? 'Đã cập nhật hồ sơ!' : 'Profile updated!', 'success');
    } catch {
      toast(lang === 'vi' ? 'Cập nhật thất bại' : 'Update failed', 'error');
    } finally { setSaving(false); }
  };

  if (!user) return null;

  return (
    <section className="dashboard-section">
      <div style={{ marginBottom: '32px' }}>
        <button className="btn-ghost" onClick={() => navigate('/dashboard')} style={{ marginBottom: '20px' }}>
          <ArrowLeft className="w-4 h-4" /> Dashboard
        </button>
        <h1 style={{ fontSize: '28px', marginBottom: '8px' }}>{lang === 'vi' ? 'Hồ sơ cá nhân' : 'Profile'}</h1>
        <p className="text-muted">{lang === 'vi' ? 'Quản lý thông tin tài khoản của bạn' : 'Manage your account information'}</p>
      </div>

      <div style={{ display: 'grid', gap: '20px', maxWidth: '600px' }}>
        {/* Account Info */}
        <div className="ai-section">
          <div className="ai-section-header">
            <h3><User className="w-4 h-4" /> {lang === 'vi' ? 'THÔNG TIN TÀI KHOẢN' : 'ACCOUNT INFO'}</h3>
          </div>
          <div className="ai-section-body">
            <div className="form-group">
              <label>{lang === 'vi' ? 'Họ và tên' : 'Full name'}</label>
              <input type="text" value={name} onChange={e => setName(e.target.value)} placeholder="Nguyễn Văn A" />
            </div>
            <div className="form-group">
              <label>Email</label>
              <input type="email" value={user.email} disabled style={{ opacity: 0.6, cursor: 'not-allowed' }} />
            </div>
            <button className="btn-primary" onClick={handleSave} disabled={saving} style={{ marginTop: '8px' }}>
              {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : (lang === 'vi' ? 'Lưu thay đổi' : 'Save changes')}
            </button>
          </div>
        </div>

        {/* Plan Info */}
        <div className="ai-section">
          <div className="ai-section-header">
            <h3><Crown className="w-4 h-4" /> {lang === 'vi' ? 'GÓI SỬ DỤNG' : 'PLAN'}</h3>
          </div>
          <div className="ai-section-body">
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
              <div className="plan-badge" style={{ fontSize: '13px', padding: '8px 16px' }}>
                {user.plan.toUpperCase()}
              </div>
              {user.monthly_minutes_limit >= 9999 && (
                <span style={{ fontSize: '13px', color: 'var(--muted)' }}>
                  {lang === 'vi' ? 'Không giới hạn phút' : 'Unlimited minutes'}
                </span>
              )}
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div style={{ padding: '16px', background: 'var(--input-bg)', borderRadius: '10px', border: '1px solid var(--border)' }}>
                <div style={{ fontSize: '22px', fontWeight: 700, marginBottom: '4px' }}>{user.monthly_minutes_used}</div>
                <div style={{ fontSize: '12px', color: 'var(--muted)' }}>{lang === 'vi' ? 'Phút đã dùng' : 'Minutes used'}</div>
              </div>
              <div style={{ padding: '16px', background: 'var(--input-bg)', borderRadius: '10px', border: '1px solid var(--border)' }}>
                <div style={{ fontSize: '22px', fontWeight: 700, marginBottom: '4px' }}>
                  {user.monthly_minutes_limit >= 9999 ? '∞' : user.monthly_minutes_limit}
                </div>
                <div style={{ fontSize: '12px', color: 'var(--muted)' }}>{lang === 'vi' ? 'Giới hạn' : 'Limit'}</div>
              </div>
            </div>
            <button className="btn-ghost" onClick={() => navigate('/pricing')} style={{ marginTop: '16px', width: '100%' }}>
              <CreditCard className="w-4 h-4" /> {lang === 'vi' ? 'Xem bảng giá' : 'View pricing'}
            </button>
          </div>
        </div>

        {/* Security */}
        <div className="ai-section">
          <div className="ai-section-header">
            <h3><Shield className="w-4 h-4" /> {lang === 'vi' ? 'BẢO MẬT' : 'SECURITY'}</h3>
          </div>
          <div className="ai-section-body">
            <p style={{ fontSize: '14px', color: 'var(--muted)', marginBottom: '12px' }}>
              {lang === 'vi' ? 'Đổi mật khẩu thông qua email của bạn.' : 'Change password through your email.'}
            </p>
            <button className="btn-ghost" onClick={() => toast(lang === 'vi' ? 'Tính năng sẽ sớm ra mắt' : 'Coming soon', 'info')}>
              {lang === 'vi' ? 'Đổi mật khẩu' : 'Change password'}
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}


function PricingPage({ navigate }: { navigate: (to: string) => void }) {
  const { user } = useAuth();
  const { lang } = useLang();

  return (
    <section className="dashboard-section">
      <div style={{ marginBottom: '32px' }}>
        {user && (
          <button className="btn-ghost" onClick={() => navigate('/dashboard')} style={{ marginBottom: '24px' }}>
            <ArrowLeft className="w-4 h-4" /> Dashboard
          </button>
        )}
        <h1 style={{ fontSize: '32px', marginBottom: '8px' }}>{lang === 'vi' ? 'Bảng giá' : 'Pricing'}</h1>
        <p className="text-muted" style={{ maxWidth: '500px' }}>
          {lang === 'vi'
            ? 'TranscribeAI hiện tại hoàn toàn miễn phí. Nếu thấy hữu ích, bạn có thể ủng hộ để duy trì dự án.'
            : 'TranscribeAI is currently free. If you find it useful, you can donate to help keep it running.'}
        </p>
      </div>

      <div className="pricing-grid" style={{ gridTemplateColumns: 'repeat(2, 1fr)', maxWidth: '700px', margin: '0 auto', gap: '20px', alignItems: 'stretch' }}>
        {/* Free Plan */}
        <div className="pricing-card">
          <h3>{lang === 'vi' ? 'Miễn phí' : 'Free'}</h3>
          <div className="pricing-price">$0<span> / {lang === 'vi' ? 'mãi mãi' : 'forever'}</span></div>
          <ul>
            <li>✓ {lang === 'vi' ? 'Chuyển đổi không giới hạn' : 'Unlimited transcription'}</li>
            <li>✓ {lang === 'vi' ? 'AI tóm tắt' : 'AI summary'}</li>
            <li>✓ {lang === 'vi' ? 'Hỏi đáp AI' : 'AI Q&A'}</li>
            <li>✓ {lang === 'vi' ? 'Trích xuất công việc' : 'Action items'}</li>
            <li>✓ {lang === 'vi' ? 'Xuất SRT / TXT' : 'Export SRT / TXT'}</li>
          </ul>
          <button className="btn-ghost" style={{ width: '100%', marginTop: 'auto' }} disabled>
            {lang === 'vi' ? 'Đang sử dụng' : 'Current plan'}
          </button>
        </div>

        {/* Donate */}
        <div className="pricing-card featured">
          <div className="pricing-badge">{lang === 'vi' ? 'Ủng hộ' : 'Support'}</div>
          <h3>Buy me a coffee</h3>
          <div className="pricing-price" style={{ fontSize: '24px', marginBottom: '16px' }}>
            {lang === 'vi' ? 'Tuỳ tâm' : 'Any amount'} <Heart className="w-5 h-5" style={{ display: 'inline', color: 'var(--error)' }} />
          </div>
          <ul>
            <li>{lang === 'vi' ? 'Giúp duy trì máy chủ' : 'Helps keep servers running'}</li>
            <li>{lang === 'vi' ? 'Phát triển tính năng mới' : 'Fund new features'}</li>
            <li>{lang === 'vi' ? 'Không ảnh hưởng tính năng' : 'No feature restrictions'}</li>
          </ul>
          <div style={{ display: 'grid', gap: '10px', marginTop: 'auto' }}>
            <div style={{ padding: '16px', background: 'var(--input-bg)', borderRadius: '10px', border: '1px solid var(--border)', textAlign: 'center' }}>
              <img src="https://img.vietqr.io/image/970423-0968999999-compact2.jpg?amount=50000&addInfo=TranscribeAI%20Donation" alt="QR" style={{ width: '100%', maxWidth: '180px', borderRadius: '8px' }} />
              <p style={{ marginTop: '8px', fontSize: '12px', color: 'var(--muted)' }}>Vietcombank</p>
            </div>
            <button className="btn-primary" style={{ width: '100%' }}>
              Donate PayPal
            </button>
          </div>
        </div>
      </div>

      <div style={{ textAlign: 'center', marginTop: '40px' }}>
        <p style={{ fontSize: '14px', color: 'var(--muted)' }}>
          {lang === 'vi' ? 'Mọi đóng góp dù nhỏ đều giúp dự án phát triển. Cảm ơn bạn! ❤️' : 'Every contribution helps. Thank you! ❤️'}
        </p>
      </div>

    </section>
  );
}


function FeedbackPage({ navigate }: { navigate: (to: string) => void }) {
  const { user } = useAuth();
  const { lang } = useLang();
  return (
    <section className="dashboard-section">
      <div style={{ marginBottom: '32px' }}>
        <button className="btn-ghost" onClick={() => navigate(user ? '/dashboard' : '/')} style={{ marginBottom: '24px' }}>
          <ArrowLeft className="w-4 h-4" /> {user ? 'Dashboard' : t('nav_pricing', lang)}
        </button>
        <h1 style={{ fontSize: '32px', marginBottom: '8px' }}>{t('fb_title', lang)}</h1>
        <p className="text-muted" style={{ maxWidth: '500px' }}>{t('fb_subtitle', lang)}</p>
      </div>
      <FeedbackSection />
    </section>
  );
}


function FeedbackSection() {
  const { lang } = useLang();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [fbType, setFbType] = useState('general');
  const [message, setMessage] = useState('');
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);

  const handleSend = async () => {
    if (!message.trim()) { toast(t('fb_empty', lang), 'error'); return; }
    setSending(true);
    try {
      await feedbackApi.send({ name, email, feedback_type: fbType, message });
      toast(t('fb_success', lang), 'success');
      setMessage(''); setName(''); setEmail(''); setFbType('general');
      setSent(true);
      setTimeout(() => setSent(false), 5000);
    } catch {
      toast(t('fb_fail', lang), 'error');
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="feedback-section">
      <div className="feedback-header">
        <MessageCircle className="w-5 h-5" style={{ color: 'var(--accent)' }} />
        <h2>{t('fb_title', lang)}</h2>
      </div>
      <p className="feedback-subtitle">{t('fb_subtitle', lang)}</p>
      <div className="feedback-note">
        <p>{t('fb_note', lang)}</p>
      </div>
      <div className="feedback-form">
        <div className="feedback-row">
          <input
            type="text"
            placeholder={t('fb_name', lang)}
            value={name}
            onChange={e => setName(e.target.value)}
            className="feedback-input"
          />
          <input
            type="email"
            placeholder={t('fb_email', lang)}
            value={email}
            onChange={e => setEmail(e.target.value)}
            className="feedback-input"
          />
        </div>
        <div className="feedback-type-row">
          {(['general', 'bug', 'feature', 'other'] as const).map(tp => (
            <button
              key={tp}
              className={`feedback-type-btn ${fbType === tp ? 'active' : ''}`}
              onClick={() => setFbType(tp)}
            >
              {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
              {t(`fb_type_${tp}` as any, lang)}
            </button>
          ))}
        </div>
        <textarea
          placeholder={t('fb_message', lang)}
          value={message}
          onChange={e => setMessage(e.target.value)}
          className="feedback-textarea"
          rows={4}
        />
        <button
          className="btn-primary feedback-send-btn"
          onClick={handleSend}
          disabled={sending || !message.trim()}
        >
          {sending ? <><Loader2 className="w-4 h-4 animate-spin" /> {t('fb_sending', lang)}</> : <><Send className="w-4 h-4" /> {t('fb_send', lang)}</>}
        </button>
        {sent && <p className="feedback-thanks">✅ {t('fb_success', lang)}</p>}
      </div>
    </div>
  );
}


function StudioPage({ navigate }: { navigate: (to: string) => void }) {
  const { lang } = useLang();
  const [file, setFile] = useState<File | null>(null);
  const [mode, setMode] = useState('standard');
  const [status, setStatus] = useState<'idle' | 'uploading' | 'processing' | 'completed'>('idle');
  const [progress, setProgress] = useState(0);
  const [progressDetail, setProgressDetail] = useState('');
  const [jobId, setJobId] = useState<string | null>(null);

  const handleFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      if (e.target.files[0].size > 200 * 1024 * 1024) { toast(t('studio_file_too_big', lang), 'error'); return; }
      setFile(e.target.files[0]);
    }
  };

  const startTranscription = async () => {
    if (!file) return;
    setStatus('uploading');
    setProgress(0);
    setProgressDetail(t('studio_upload_detail', lang));
    try {
      const res = await jobsApi.create(file, mode, undefined, (p) => {
        setProgress(p);
        setProgressDetail(`${t('studio_upload_pct', lang)} ${p}%`);
      });
      setJobId(res.data.job_id);
      setStatus('processing');
      setProgress(5);
      setProgressDetail(t('studio_init', lang));
    } catch (err: unknown) {
      setStatus('idle');
      const axErr = err as { response?: { data?: { detail?: string } }; message?: string };
      const msg = axErr.response?.data?.detail || axErr.message || t('studio_server_error', lang);
      toast(msg, 'error');
    }
  };

  // Poll for real progress
  useEffect(() => {
    if (status !== 'processing' || !jobId) return;
    const iv = setInterval(async () => {
      try {
        const res = await jobsApi.progress(jobId);
        const { percent, step, detail, status: jobStatus } = res.data;
        setProgress(percent);
        setProgressDetail(detail || step);
        if (jobStatus === 'completed' || step === 'done') {
          clearInterval(iv);
          setStatus('completed');
          toast(t('studio_done', lang), 'success');
          navigate(`/results/${jobId}`);
        } else if (jobStatus === 'failed' || step === 'failed') {
          clearInterval(iv);
          setStatus('idle');
          toast(detail || t('studio_fail', lang), 'error');
        }
      } catch { /* retry */ }
    }, 1000);
    return () => clearInterval(iv);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status, jobId]);

  return (
    <section className="hero">
      <div className="badge"><span className="badge-dot" /> {t('studio_badge', lang)}</div>
      <h1>{t('studio_h1_1', lang)}<br /><span className="gradient-text">{t('studio_h1_2', lang)}</span></h1>
      <p className="subtitle">{t('studio_subtitle', lang)}</p>

      <div className="upload-wrap">
        <div className="upload-card">
          {status === 'idle' ? (
            <>
              <div className="upload-zone" onClick={() => document.getElementById('fileInput')?.click()}>
                <input type="file" id="fileInput" className="hidden" onChange={handleFile} accept="audio/*,video/*" />
                <div className="upload-icon-ring">
                  <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
                    <path d="M12 16V8M12 8l-3 3M12 8l3 3" stroke="#7eb3ff" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                    <path d="M20 16.5A4.5 4.5 0 0017.5 8H16.3A7 7 0 104 15.3" stroke="#7eb3ff" strokeWidth="1.8" strokeLinecap="round" />
                  </svg>
                </div>
                <div className="upload-label">{file ? file.name : t('studio_drop', lang)}</div>
                <div className="upload-hint">MP3 · WAV · MP4 · M4A&nbsp;•&nbsp;{t('studio_hint', lang)}</div>
              </div>

              <div className="toolbar">
                <button className={`tool-chip ${mode === 'standard' ? 'active' : ''}`} onClick={() => setMode('standard')}>
                  <FileText className="w-3.5 h-3.5" /> Standard
                </button>
                <button className={`tool-chip ${mode === 'meeting' ? 'active' : ''}`} onClick={() => setMode('meeting')}>
                  <ListChecks className="w-3.5 h-3.5" /> Meeting
                </button>
                <button className={`tool-chip ${mode === 'lecture' ? 'active' : ''}`} onClick={() => setMode('lecture')}>
                  <Sparkles className="w-3.5 h-3.5" /> Lecture
                </button>
                <span className="toolbar-spacer" />
                <button className="btn-run" onClick={startTranscription} disabled={!file}>
                  <Zap className="w-4 h-4" /> {t('studio_start', lang)}
                </button>
              </div>
            </>
          ) : (
            <div className="processing-state">
              <div className="progress-ring-wrapper">
                <svg className="progress-ring" viewBox="0 0 120 120">
                  <circle className="progress-ring-bg" cx="60" cy="60" r="52" />
                  <circle className="progress-ring-fill" cx="60" cy="60" r="52"
                    strokeDasharray={`${2 * Math.PI * 52}`}
                    strokeDashoffset={`${2 * Math.PI * 52 * (1 - progress / 100)}`}
                  />
                </svg>
                <span className="progress-ring-text">{progress}%</span>
              </div>
              <h2>{status === 'uploading' ? t('studio_uploading', lang) : progress >= 90 ? t('studio_ai_analyzing', lang) : t('studio_processing', lang)}</h2>
              <p className="text-muted">{progressDetail}</p>
              <div className="progress-bar" style={{ width: '100%', maxWidth: '400px' }}>
                <div className="progress-fill" style={{ width: `${progress}%` }} />
              </div>
              <div className="progress-steps">
                <span className={`progress-step ${progress >= 5 ? 'active' : ''} ${progress >= 10 ? 'done' : ''}`}>{t('studio_step_model', lang)}</span>
                <span className="progress-step-dot">→</span>
                <span className={`progress-step ${progress >= 10 ? 'active' : ''} ${progress >= 20 ? 'done' : ''}`}>{t('studio_step_decode', lang)}</span>
                <span className="progress-step-dot">→</span>
                <span className={`progress-step ${progress >= 20 ? 'active' : ''} ${progress >= 75 ? 'done' : ''}`}>{t('studio_step_transcribe', lang)}</span>
                <span className="progress-step-dot">→</span>
                <span className={`progress-step ${progress >= 85 ? 'active' : ''} ${progress >= 90 ? 'done' : ''}`}>{t('studio_step_save', lang)}</span>
                <span className="progress-step-dot">→</span>
                <span className={`progress-step ${progress >= 90 ? 'active' : ''} ${progress >= 100 ? 'done' : ''}`}>{t('studio_step_ai', lang)}</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}


/* ─── AI Text Formatter ─── */
function cleanAIString(raw: string): string {
  if (!raw) return '';
  let s = raw.trim();
  // Strip JSON-like wrappers: {"...","..."} or ["...","..."]
  if ((s.startsWith('{') && s.endsWith('}')) || (s.startsWith('[') && s.endsWith(']'))) {
    s = s.slice(1, -1);
  }
  // Split on "," (JSON array separator) and rejoin as paragraphs
  const parts = s.split(/",\s*"/);
  s = parts.map(p => p.replace(/^"|"$/g, '').trim()).filter(Boolean).join('\n\n');
  // Remove leftover quotes at boundaries
  s = s.replace(/^"|"$/g, '');
  return s;
}

function formatAIText(text: string): React.ReactNode[] {
  if (!text) return [];
  const cleaned = cleanAIString(text);
  const lines = cleaned.split('\n');
  return lines.map((line, i) => {
    const trimmed = line.trim();
    if (!trimmed) return <br key={i} />;
    // Headings: lines ending with ":" or starting with "##"
    if (trimmed.match(/^#{1,3}\s/) || (trimmed.endsWith(':') && trimmed.length < 80 && !trimmed.includes('. '))) {
      const headingText = trimmed.replace(/^#{1,3}\s*/, '').replace(/:$/, '');
      return <h4 key={i} className="ai-heading">{headingText.toUpperCase()}</h4>;
    }
    // Bold: **text**
    const parts = trimmed.split(/(\*\*.*?\*\*)/g);
    const formatted = parts.map((part, j) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={j}>{part.slice(2, -2)}</strong>;
      }
      return part;
    });
    // List items: lines starting with - or • or *
    if (trimmed.match(/^[-•*]\s/)) {
      return <li key={i} className="ai-list-item">{formatted.map((f) => typeof f === 'string' ? f.replace(/^[-•*]\s/, '') : f)}</li>;
    }
    // Numbered list: 1. 2. etc
    if (trimmed.match(/^\d+[.)]\s/)) {
      return <li key={i} className="ai-list-item numbered">{formatted}</li>;
    }
    return <p key={i} className="ai-paragraph">{formatted}</p>;
  });
}

function formatTime(s: number): string {
  const m = Math.floor(s / 60);
  const sec = Math.floor(s % 60);
  return `${m.toString().padStart(2, '0')}:${sec.toString().padStart(2, '0')}`;
}

function ResultsPage({ navigate, jobId }: { navigate: (to: string) => void; jobId: string }) {
  const { lang } = useLang();
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [job, setJob] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [summary, setSummary] = useState<any>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [chatMsgs, setChatMsgs] = useState<any[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [actions, setActions] = useState<any[]>([]);
  const [regenLoading, setRegenLoading] = useState(false);
  const [showTranscript, setShowTranscript] = useState(false);
  const [showActions, setShowActions] = useState(true);
  const [jobProgress, setJobProgress] = useState(0);
  const [jobProgressDetail, setJobProgressDetail] = useState('');
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const loadJob = async () => {
      try {
        const res = await jobsApi.get(jobId);
        setJob(res.data);
        if (res.data.status !== 'completed' && res.data.status !== 'failed') {
          // Poll progress instead of just status
          const iv = setInterval(async () => {
            try {
              const pr = await jobsApi.progress(jobId);
              setJobProgress(pr.data.percent);
              setJobProgressDetail(pr.data.detail || pr.data.step);
              if (pr.data.status === 'completed' || pr.data.step === 'done') {
                clearInterval(iv);
                const r = await jobsApi.get(jobId);
                setJob(r.data);
                if (r.data.summary) setSummary(r.data.summary);
                if (r.data.action_items) setActions(r.data.action_items);
                aiApi.chatHistory(jobId).then(r => setChatMsgs(r.data)).catch(() => { });
              } else if (pr.data.status === 'failed') {
                clearInterval(iv);
                const r = await jobsApi.get(jobId);
                setJob(r.data);
              }
            } catch { /* retry */ }
          }, 1000);
          setLoading(false);
          return () => clearInterval(iv);
        }
        if (res.data.summary) setSummary(res.data.summary);
        if (res.data.action_items) setActions(res.data.action_items);
        // Auto-load chat history
        aiApi.chatHistory(jobId).then(r => setChatMsgs(r.data)).catch(() => { });
      } catch { toast(t('res_load_fail', lang), 'error'); navigate('/dashboard'); }
      finally { setLoading(false); }
    };
    loadJob();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jobId]);

  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [chatMsgs]);

  const sendChat = async () => {
    if (!chatInput.trim() || chatLoading) return;
    const msg = chatInput;
    setChatInput('');
    setChatMsgs(p => [...p, { role: 'user', content: msg, id: 'temp-' + Date.now() }]);
    setChatLoading(true);
    try {
      const res = await aiApi.chat(jobId, msg);
      setChatMsgs(p => [...p, { role: 'assistant', content: res.data.answer, id: 'ai-' + Date.now() }]);
    } catch { toast(t('res_chat_fail', lang), 'error'); }
    finally { setChatLoading(false); }
  };

  const regenSummary = async (targetLang?: string) => {
    setRegenLoading(true);
    try {
      const res = await aiApi.regenerateSummary(jobId, targetLang || lang);
      setSummary(res.data);
      toast(t('res_regen_success', lang), 'success');
    } catch { toast(t('res_regen_fail', lang), 'error'); }
    finally { setRegenLoading(false); }
  };

  // Auto-regenerate summary in new language when user toggles lang
  const prevLangRef = React.useRef(lang);
  React.useEffect(() => {
    if (prevLangRef.current !== lang && summary) {
      prevLangRef.current = lang;
      regenSummary(lang);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lang]);

  const extractActions = async () => {
    setRegenLoading(true);
    try {
      const res = await aiApi.extractActions(jobId);
      setActions(res.data);
      toast(`${lang === 'vi' ? 'Trích xuất' : 'Extracted'} ${res.data.length} ${t('res_extract_success', lang)}`, 'success');
    } catch { toast(t('res_extract_fail', lang), 'error'); }
    finally { setRegenLoading(false); }
  };

  const toggleAction = async (actionId: string, completed: boolean) => {
    try {
      await aiApi.updateAction(jobId, actionId, { is_completed: !completed });
      setActions(a => a.map(x => x.id === actionId ? { ...x, is_completed: !completed } : x));
    } catch { toast(t('res_update_fail', lang), 'error'); }
  };

  const copyTranscript = () => {
    if (job?.transcript) {
      navigator.clipboard.writeText(job.transcript);
      toast(t('res_copied', lang), 'success');
    }
  };

  if (loading) return <div className="page-loader"><Loader2 className="w-10 h-10 animate-spin text-accent" /></div>;
  if (!job) return null;

  if (job.status !== 'completed') {
    return (
      <section className="results-section">
        <div className="processing-state" style={{ padding: '80px 0' }}>
          {job.status === 'failed' ? (
            <>
              <h2>{t('res_failed_title', lang)}</h2>
              <p className="text-muted">{job.error || t('res_failed_detail', lang)}</p>
            </>
          ) : (
            <>
              <div className="progress-ring-wrapper">
                <svg className="progress-ring" viewBox="0 0 120 120">
                  <circle className="progress-ring-bg" cx="60" cy="60" r="52" />
                  <circle className="progress-ring-fill" cx="60" cy="60" r="52"
                    strokeDasharray={`${2 * Math.PI * 52}`}
                    strokeDashoffset={`${2 * Math.PI * 52 * (1 - jobProgress / 100)}`}
                  />
                </svg>
                <span className="progress-ring-text">{jobProgress}%</span>
              </div>
              <h2>{jobProgress >= 90 ? t('res_analyzing', lang) : t('res_processing', lang)}</h2>
              <p className="text-muted">{jobProgressDetail || t('res_wait', lang)}</p>
              <div className="progress-bar" style={{ width: '100%', maxWidth: '400px' }}>
                <div className="progress-fill" style={{ width: `${jobProgress}%` }} />
              </div>
            </>
          )}
          <button className="btn-ghost" onClick={() => navigate('/dashboard')} style={{ marginTop: 16 }}>
            <ArrowLeft className="w-4 h-4" /> {t('res_back_dash', lang)}
          </button>
        </div>
      </section>
    );
  }

  const promptSuggestions = [
    t('res_suggest_1', lang),
    t('res_suggest_2', lang),
    t('res_suggest_3', lang),
    t('res_suggest_4', lang),
  ];

  return (
    <section className="results-section">
      {/* ── Header ── */}
      <div className="results-header">
        <div className="results-header-row">
          <button className="btn-ghost" onClick={() => navigate('/dashboard')}><ArrowLeft className="w-4 h-4" /> Dashboard</button>
          <div className="results-header-actions">
            <button className="btn-ghost" onClick={copyTranscript}><Copy className="w-4 h-4" /> {t('res_copy', lang)}</button>
            <button className="btn-ghost" onClick={() => setShowTranscript(!showTranscript)}>
              {showTranscript ? <PanelRightClose className="w-4 h-4" /> : <PanelRightOpen className="w-4 h-4" />}
              {showTranscript ? t('res_hide_transcript', lang) : t('res_show_transcript', lang)}
            </button>
          </div>
        </div>
        <div className="results-title">
          <h2>{job.original_filename}</h2>
          <div className="results-meta">
            <span><CheckCircle2 className="w-3.5 h-3.5" /> {(job.overall_confidence * 100).toFixed(1)}%</span>
            <span><Clock className="w-3.5 h-3.5" /> {job.processing_time_s}s</span>
            <span><Globe className="w-3.5 h-3.5" /> {job.language_detected}</span>
            <span className="badge-mode">{job.mode}</span>
          </div>
        </div>
      </div>

      {/* ── 2-Panel Body ── */}
      <div className={`results-body ${showTranscript ? '' : 'full-width'}`}>

        {/* ── Left Column: Summary + Actions ── */}
        <div className="ai-panel ai-panel-left">

          {/* Summary Section */}
          <div className="ai-section">
            <div className="ai-section-header">
              <h3><Sparkles className="w-4 h-4" /> AI SUMMARY</h3>
              <button className="btn-ghost btn-sm" onClick={() => regenSummary()} disabled={regenLoading}>
                {regenLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
                {summary ? t('res_regen', lang) : t('res_gen_summary', lang)}
              </button>
            </div>
            {summary ? (
              <div className="ai-section-body">
                {summary.summary && (
                  <div className="ai-block">
                    <div className="ai-block-title">{t('res_summary_label', lang)}</div>
                    <div className="ai-text">{formatAIText(summary.summary)}</div>
                  </div>
                )}
                {summary.key_points?.length > 0 && (
                  <div className="ai-block">
                    <div className="ai-block-title">{t('res_keypoints', lang)}</div>
                    <ul className="ai-key-points">
                      {summary.key_points.map((kp: string, i: number) => (
                        <li key={i}>{formatAIText(kp)}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {summary.conclusion && (
                  <div className="ai-block">
                    <div className="ai-block-title">{t('res_conclusion', lang)}</div>
                    <div className="ai-text">{formatAIText(summary.conclusion)}</div>
                  </div>
                )}
                <div className="ai-model-tag">Model: {summary.llm_model}{summary.review_passes ? ` · ${summary.review_passes} review pass(es)` : ''}</div>
              </div>
            ) : (
              <div className="ai-empty">
                <Sparkles className="w-8 h-8" style={{ opacity: 0.2 }} />
                <p>{t('res_summary_empty', lang)}</p>
              </div>
            )}
          </div>

          {/* Action Items Section */}
          <div className="ai-section">
            <div className="ai-section-header">
              <button className="ai-collapse-btn" onClick={() => setShowActions(!showActions)}>
                {showActions ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                <h3><ListChecks className="w-4 h-4" /> {t('res_tasks', lang)}</h3>
                {actions.length > 0 && <span className="ai-count-badge">{actions.length}</span>}
              </button>
              <button className="btn-ghost btn-sm" onClick={extractActions} disabled={regenLoading}>
                {regenLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <ListChecks className="w-3.5 h-3.5" />}
                {actions.length ? t('res_extract_again', lang) : t('res_extract', lang)}
              </button>
            </div>
            {showActions && (
              actions.length > 0 ? (
                <div className="ai-section-body">
                  {actions.map(a => (
                    <div key={a.id} className={`action-card ${a.is_completed ? 'completed' : ''}`}>
                      <button className="action-check" onClick={() => toggleAction(a.id, a.is_completed)}>
                        {a.is_completed ? <CheckCircle2 className="w-5 h-5 text-emerald-400" /> : <div className="action-unchecked" />}
                      </button>
                      <div className="action-info">
                        <div className="action-task">{a.task_description}</div>
                        <div className="action-meta">
                          <span>👤 {a.assignee}</span>
                          <span>📅 {a.deadline}</span>
                          <span className={`priority-badge ${a.priority}`}>{a.priority}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="ai-empty small">
                  <p>{t('res_tasks_empty', lang)}</p>
                </div>
              )
            )}
          </div>
        </div>

        {/* ── Right Column: Chat Q&A ── */}
        <div className="ai-panel ai-panel-right">
          <div className="ai-section chat-section chat-sticky">
            <div className="ai-section-header">
              <h3><MessageSquare className="w-4 h-4" /> {t('res_chat_title', lang)}</h3>
            </div>
            <div className="chat-messages">
              {chatMsgs.length === 0 && (
                <div className="chat-welcome-compact">
                  <p>{t('res_chat_welcome', lang)}</p>
                  <div className="chat-suggestions">
                    {promptSuggestions.map(q => (
                      <button key={q} className="suggestion-chip" onClick={() => setChatInput(q)}>{q}</button>
                    ))}
                  </div>
                </div>
              )}
              {chatMsgs.map((m, i) => (
                <div key={m.id || i} className={`chat-msg ${m.role}`}>
                  <div className="chat-msg-content">
                    {m.role === 'assistant' ? formatAIText(m.content) : m.content}
                  </div>
                </div>
              ))}
              {chatLoading && (
                <div className="chat-msg assistant">
                  <div className="chat-msg-content"><Loader2 className="w-4 h-4 animate-spin" /> {t('res_chat_thinking', lang)}</div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>
            <div className="chat-input-bar">
              <input
                value={chatInput}
                onChange={e => setChatInput(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendChat(); } }}
                placeholder={t('res_chat_placeholder', lang)}
                disabled={chatLoading}
              />
              <button onClick={sendChat} disabled={!chatInput.trim() || chatLoading} className="chat-send-btn">
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        {/* ── Right: Transcript Panel ── */}
        {showTranscript && (
          <div className="transcript-panel">
            <div className="transcript-panel-header">
              <h3><FileText className="w-4 h-4" /> TRANSCRIPT</h3>
              <button className="btn-ghost btn-sm" onClick={copyTranscript}><Copy className="w-3.5 h-3.5" /></button>
            </div>
            <div className="transcript-panel-body">
              {job.segments?.length > 0 ? (
                <div className="segments-list">
                  {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                  {(job.segments as any[]).map((s: any, i: number) => (
                    <div key={i} className="segment-row">
                      <span className="segment-time">{formatTime(s.start)}</span>
                      <span className="segment-text">{s.text}</span>
                      <span className={`segment-conf ${s.confidence > 0.8 ? 'high' : s.confidence > 0.5 ? 'med' : 'low'}`}>
                        {(s.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="transcript-full">{job.transcript}</div>
              )}
            </div>
          </div>
        )}
      </div>
    </section>
  );
}



function LandingPage({ navigate }: { navigate: (to: string) => void }) {
  const { lang } = useLang();
  return (
    <>
      <section className="hero">
        <div className="badge"><span className="badge-dot" /> {t('land_badge', lang)}</div>
        <h1>{t('land_h1_1', lang)}<br />{t('land_h1_2', lang)} <span className="gradient-text">{t('land_h1_highlight', lang)}</span></h1>
        <p className="subtitle">
          {t('land_subtitle', lang)}
        </p>
        <div style={{ display: 'flex', gap: '16px', justifyContent: 'center', marginTop: '32px' }}>
          <button className="btn-primary" style={{ padding: '16px 40px', fontSize: '16px' }} onClick={() => navigate('/register')}>
            {t('land_cta', lang)}
          </button>
          <button className="btn-ghost" style={{ padding: '16px 40px', fontSize: '16px' }} onClick={() => navigate('/login')}>
            {t('land_signin', lang)}
          </button>
        </div>
      </section>

      <div className="divider" />

      {/* Features */}
      <section className="section">
        <div className="section-label"><Sparkles className="w-3 h-3" /> {t('land_feat_label', lang)}</div>
        <h2 className="section-title">{t('land_feat_title', lang)}<br />{t('land_feat_title2', lang)}</h2>
        <div className="features-grid">
          <div className="feat-card">
            <div className="feat-icon"><Mic className="w-5 h-5" style={{ color: 'var(--accent)' }} /></div>
            <div className="feat-title">{t('land_feat1_title', lang)}</div>
            <div className="feat-desc">{t('land_feat1_desc', lang)}</div>
          </div>
          <div className="feat-card">
            <div className="feat-icon"><Sparkles className="w-5 h-5" style={{ color: 'var(--accent)' }} /></div>
            <div className="feat-title">{t('land_feat2_title', lang)}</div>
            <div className="feat-desc">{t('land_feat2_desc', lang)}</div>
          </div>
          <div className="feat-card">
            <div className="feat-icon"><MessageSquare className="w-5 h-5" style={{ color: 'var(--accent)' }} /></div>
            <div className="feat-title">{t('land_feat3_title', lang)}</div>
            <div className="feat-desc">{t('land_feat3_desc', lang)}</div>
          </div>
          <div className="feat-card">
            <div className="feat-icon"><ListChecks className="w-5 h-5" style={{ color: 'var(--accent)' }} /></div>
            <div className="feat-title">{t('land_feat4_title', lang)}</div>
            <div className="feat-desc">{t('land_feat4_desc', lang)}</div>
          </div>
          <div className="feat-card">
            <div className="feat-icon"><Globe className="w-5 h-5" style={{ color: 'var(--accent)' }} /></div>
            <div className="feat-title">{t('land_feat5_title', lang)}</div>
            <div className="feat-desc">{t('land_feat5_desc', lang)}</div>
          </div>
          <div className="feat-card">
            <div className="feat-icon"><Share2 className="w-5 h-5" style={{ color: 'var(--accent)' }} /></div>
            <div className="feat-title">{t('land_feat6_title', lang)}</div>
            <div className="feat-desc">{t('land_feat6_desc', lang)}</div>
          </div>
        </div>
      </section>

      <div className="divider" />

      {/* Donation Section */}
      <section className="section">
        <div className="section-label"><Heart className="w-3 h-3" /> {t('land_donate_label', lang)}</div>
        <h2 className="section-title">{t('land_donate_title', lang)}</h2>
        <p className="subtitle" style={{ margin: '0 auto 40px' }}>
          {t('land_donate_desc', lang)}
        </p>
        <div className="pricing-grid" style={{ gridTemplateColumns: 'minmax(0, 500px)', justifyContent: 'center' }}>
          <div className="pricing-card featured" style={{ textAlign: 'center' }}>
            <div className="pricing-badge">{t('land_donate_badge', lang)}</div>
            <h3>{t('land_donate_h3', lang)}</h3>
            <p className="text-muted" style={{ marginBottom: '24px' }}>{t('land_donate_sub', lang)}</p>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '24px' }}>
              <div style={{ padding: '20px', background: 'var(--input-bg)', borderRadius: '12px', border: '1px solid var(--border)' }}>
                <img src="https://img.vietqr.io/image/970423-0968999999-compact2.jpg?amount=50000&addInfo=TranscribeAI%20Donation" alt="MoMo" style={{ width: '100%', borderRadius: '8px' }} />
                <p style={{ marginTop: '12px', fontSize: '13px' }}>Vietcombank</p>
              </div>
              <div style={{ padding: '20px', background: 'var(--input-bg)', borderRadius: '12px', border: '1px solid var(--border)', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                <p style={{ fontSize: '14px', marginBottom: '12px' }}>{t('land_donate_or', lang)}</p>
                <button className="btn-primary" style={{ width: '100%' }}>Donate PayPal</button>
              </div>
            </div>
            <p style={{ fontSize: '12px', color: 'var(--muted)' }}>{t('land_donate_thanks', lang)}</p>
          </div>
        </div>
      </section>

      <div className="divider" />

      {/* CTA */}
      <section className="cta-section">
        <div className="cta-card">
          <h2>{t('land_cta_title', lang)}</h2>
          <p>{t('land_cta_desc1', lang)}<br />{t('land_cta_desc2', lang)}</p>
          <div style={{ display: 'flex', justifyContent: 'center', gap: '16px' }}>
            <button className="btn-primary" style={{ padding: '16px 40px' }} onClick={() => navigate('/register')}>{t('land_cta_btn', lang)}</button>
          </div>
        </div>
      </section>

      <footer>
        <div className="footer-logo">TranscribeAI</div>
        <div className="footer-links">
          <a href="/pricing">Pricing</a>
          <a href="/docs">API Docs</a>
          <a href="#">Privacy</a>
        </div>
      </footer>
    </>
  );
}


function App() {
  const { path, navigate } = useRouter();
  const { user, loading } = useAuth();

  // Route matching
  const jobIdMatch = path.match(/^\/results\/(.+)/);
  const jobId = jobIdMatch?.[1];

  // Redirect logic
  useEffect(() => {
    if (loading) return;
    if (!user && ['/dashboard', '/studio', '/profile'].includes(path)) navigate('/login');
    if (!user && path.startsWith('/results/')) navigate('/login');
    if (user && (path === '/login' || path === '/register')) navigate('/dashboard');
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, path, loading]);

  if (loading) return <div className="page-loader"><Loader2 className="w-10 h-10 animate-spin text-accent" /></div>;

  let page;
  if (path === '/login') page = <LoginPage navigate={navigate} />;
  else if (path === '/register') page = <RegisterPage navigate={navigate} />;
  else if (path === '/dashboard' && user) page = <DashboardPage navigate={navigate} />;
  else if (path === '/studio' && user) page = <StudioPage navigate={navigate} />;
  else if (path === '/profile' && user) page = <ProfilePage navigate={navigate} />;
  else if (path === '/pricing') page = <PricingPage navigate={navigate} />;
  else if (path === '/feedback') page = <FeedbackPage navigate={navigate} />;
  else if (path === '/error/500') page = <ServerErrorPage navigate={navigate} />;
  else if (path === '/error/network') page = <NetworkErrorPage navigate={navigate} />;
  else if (jobId && user) page = <ResultsPage navigate={navigate} jobId={jobId} />;
  else if (path === '/') page = <LandingPage navigate={navigate} />;
  else page = <NotFoundPage navigate={navigate} />;

  return (
    <div className="min-h-screen">
      <Navbar navigate={navigate} />
      <ErrorBoundary navigate={navigate}>
        {page}
      </ErrorBoundary>
      <ToastContainer />
    </div>
  );
}


export default function AppWithAuth() {
  const [lang, setLang] = useState(() => localStorage.getItem('lang') || 'vi');
  const toggle = () => {
    const next = lang === 'vi' ? 'en' : 'vi';
    setLang(next);
    localStorage.setItem('lang', next);
  };

  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'light');
  const toggleTheme = () => {
    const next = theme === 'light' ? 'dark' : 'light';
    setTheme(next);
    localStorage.setItem('theme', next);
  };
  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.setAttribute('data-theme', 'dark');
    } else {
      document.documentElement.removeAttribute('data-theme');
    }
  }, [theme]);

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      <LangContext.Provider value={{ lang, toggle }}>
        <AuthProvider>
          <App />
        </AuthProvider>
      </LangContext.Provider>
    </ThemeContext.Provider>
  );
}
