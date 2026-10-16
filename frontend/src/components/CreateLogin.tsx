import LoginForm from './LoginForm';
import styles from './Account.module.css';

interface Props {
  name: string;
  email: string | null;
  /** Opened from a new link after a forgotten password */
  reset: boolean;
  onSaved: () => void;
  onUnauthorized: () => void;
}

/** First screen after opening an invite link. */
export default function CreateLogin({ name, email, reset, onSaved, onUnauthorized }: Props) {
  return (
    <main className={styles.screen}>
      <div className={styles.card}>
        <h1 className={styles.title}>{reset ? 'Choose a new password' : `Welcome, ${name}`}</h1>
        <p className={styles.note}>
          {reset
            ? 'Set a new password for your Cinémathèque login. This link stops working afterwards.'
            : 'Create your login, so you can sign in on any device with your email and password. ' +
              'This invite link stops working once your login exists.'}
        </p>
        <LoginForm
          initialEmail={email}
          askCurrent={false}
          submitLabel={reset ? 'Save new password' : 'Create login'}
          onSaved={onSaved}
          onUnauthorized={onUnauthorized}
        />
      </div>
    </main>
  );
}
