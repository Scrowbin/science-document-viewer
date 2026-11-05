import { useEffect, useRef } from 'react';
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
  const statusLabel = isLoadingDocs ? 'Connecting…' : isLiveApiConnected ? 'Connected' : 'Offline';
  const statusTitle = isLoadingDocs
    ? 'Connecting to the server…'
    : isLiveApiConnected
    ? 'Connected to the library server'
    : 'Cannot reach the library server';
  const toggleRef = useRef<HTMLButtonElement>(null);

  // Escape closes the open menu and returns focus to its button.
  useEffect(() => {
    if (!showMenu) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !e.defaultPrevented) {
        e.preventDefault();
        onToggleMenu();
        toggleRef.current?.focus();
      }
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [showMenu, onToggleMenu]);

  return (
    <div className={styles.userHeaderSection} ref={menuRef}>
      {/* API Status Badge */}
      <div className={styles.apiStatusBadge} title={statusTitle} role="status">
        <span
          aria-hidden="true"
          className={
            isLoadingDocs || !isLiveApiConnected ? styles.statusDotOffline : styles.statusDotLive
          }
        />
        <span>{statusLabel}</span>
      </div>

      {isAuthenticated && user ? (
        <>
          <button
            ref={toggleRef}
            type="button"
            className={styles.userBadgeButton}
            onClick={onToggleMenu}
            title="Account Settings & Session"
            aria-haspopup="true"
            aria-expanded={showMenu}
            aria-label={`Account menu for ${user.name}`}
          >
            <span className={styles.avatarCircle} aria-hidden="true">{userInitials}</span>
            <span className={styles.userNameLabel}>{user.name}</span>
            <FaChevronDown aria-hidden="true" style={{ fontSize: 10, opacity: 0.7 }} />
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
                <FaArrowRightToBracket aria-hidden="true" /> Switch Account
              </button>
              <button
                type="button"
                className={styles.dropdownItem}
                onClick={() => { onToggleMenu(); onNavigate('/register'); }}
              >
                <FaUserPlus aria-hidden="true" /> Register New Account
              </button>
              <div className={styles.dropdownDivider} />
              <button
                type="button"
                className={`${styles.dropdownItem} ${styles.dropdownItemDanger}`}
                onClick={onLogout}
              >
                <FaRightFromBracket aria-hidden="true" /> Sign Out
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
          <FaArrowRightToBracket aria-hidden="true" /> Sign In
        </button>
      )}
    </div>
  );
}

export default UserMenu;
