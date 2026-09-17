import styles from './UserMenu.module.css';
import type { User } from '../../types/auth';
import {
  FaChevronDown,
  FaArrowRightToBracket,
  FaRightFromBracket,
  FaUserPlus,
} from 'react-icons/fa6';

export interface UserMenuProps {
  user: User | null;
  isAuthenticated: boolean;
  isLiveApiConnected: boolean;
  isLoadingDocs: boolean;
  showMenu: boolean;
  userInitials: string;
  menuRef: React.RefObject<HTMLDivElement | null>;
  onToggleMenu: () => void;
  onNavigate: (path: string) => void;
  onLogout: () => void;
}

export function UserMenu({
  user,
  isAuthenticated,
  isLiveApiConnected,
  isLoadingDocs,
  showMenu,
  userInitials,
  menuRef,
  onToggleMenu,
  onNavigate,
  onLogout,
}: UserMenuProps) {
  const statusLabel = isLoadingDocs ? 'Connecting...' : isLiveApiConnected ? 'Django API' : 'Demo Mode';
  const statusTitle = isLoadingDocs
    ? 'Connecting to backend...'
    : isLiveApiConnected
    ? 'Connected to Django Backend API'
    : 'Operating in offline / mock demo mode';

  return (
    <div className={styles.userHeaderSection} ref={menuRef}>
      {/* API Status Badge */}
      <div className={styles.apiStatusBadge} title={statusTitle}>
        <span
          className={
            isLoadingDocs || !isLiveApiConnected ? styles.statusDotOffline : styles.statusDotLive
          }
        />
        <span>{statusLabel}</span>
      </div>

      {isAuthenticated && user ? (
        <>
          <button
            type="button"
            className={styles.userBadgeButton}
            onClick={onToggleMenu}
            title="Account Settings & Session"
          >
            <span className={styles.avatarCircle}>{userInitials}</span>
            <span className={styles.userNameLabel}>{user.name}</span>
            <FaChevronDown style={{ fontSize: 10, opacity: 0.7 }} />
          </button>

          {showMenu && (
            <div className={styles.userDropdownMenu}>
              <div className={styles.dropdownUserInfo}>
                <div className={styles.dropdownName}>{user.name}</div>
                <div className={styles.dropdownEmail}>{user.email}</div>
                {user.institution && (
                  <div className={styles.dropdownInstitution}>{user.institution}</div>
                )}
              </div>
              <button
                type="button"
                className={styles.dropdownItem}
                onClick={() => { onToggleMenu(); onNavigate('/login'); }}
              >
                <FaArrowRightToBracket /> Switch Account
              </button>
              <button
                type="button"
                className={styles.dropdownItem}
                onClick={() => { onToggleMenu(); onNavigate('/register'); }}
              >
                <FaUserPlus /> Register New Account
              </button>
              <div className={styles.dropdownDivider} />
              <button
                type="button"
                className={`${styles.dropdownItem} ${styles.dropdownItemDanger}`}
                onClick={onLogout}
              >
                <FaRightFromBracket /> Sign Out
              </button>
            </div>
          )}
        </>
      ) : (
        <button
          type="button"
          className={styles.signInNavButton}
          onClick={() => onNavigate('/login')}
        >
          <FaArrowRightToBracket /> Sign In
        </button>
      )}
    </div>
  );
}

export default UserMenu;
