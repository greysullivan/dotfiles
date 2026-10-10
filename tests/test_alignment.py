import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('manage', REPO / 'manage.py')
manage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(manage)
spec = importlib.util.spec_from_file_location('align', REPO / 'align.py')
align = importlib.util.module_from_spec(spec)
spec.loader.exec_module(align)


class AlignmentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name) / 'pro'
        self.home.mkdir()

    def command(self, *args, success=True):
        result = subprocess.run(['python3', str(REPO / 'manage.py'), 'restore',
                                 '--home', str(self.home), '--portable',
                                 '--profile', 'macbookpro11-4', *args],
                                capture_output=True, text=True)
        if success:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0)
        return result

    def firefox(self):
        base = self.home / '.config/mozilla/firefox'
        active = base / 'current.default-release'
        active.mkdir(parents=True)
        (base / 'old.default').mkdir()
        (base / 'profiles.ini').write_text(
            '[Profile0]\nPath=current.default-release\nIsRelative=1\n'
            '[Profile1]\nPath=old.default\nIsRelative=1\nDefault=1\n'
            '[InstallABC]\nDefault=current.default-release\nLocked=1\n')
        return active

    def test_preview_is_read_only_and_skips_absent_firefox(self):
        before = list(self.home.rglob('*'))
        result = self.command()
        self.assertIn('Skip Firefox styling/preferences', result.stdout)
        self.assertEqual(list(self.home.rglob('*')), before)

    def test_backups_binary_assets_profile_preferences_and_repeatability(self):
        active = self.firefox()
        userjs = active / 'user.js'
        original = 'user_pref("custom.setting", 42);\nuser_pref("toolkit.legacyUserProfileCustomizations.stylesheets", false); // keep comment\n'
        userjs.write_text(original)
        userjs.chmod(0o600)
        config = self.home / '.config/i3/config'
        config.parent.mkdir(parents=True)
        config.write_text('original target desktop\n')
        config.chmod(0o600)
        self.command('--apply')
        backups = list((self.home / '.local/state/dotfiles/backups').iterdir())
        self.assertEqual(len(backups), 1)
        self.assertEqual((backups[0] / '.config/i3/config').read_text(), 'original target desktop\n')
        self.assertEqual((backups[0] / '.config/i3/config').stat().st_mode & 0o777, 0o600)
        self.assertEqual((backups[0] / userjs.relative_to(self.home)).read_text(), original)
        self.assertIn('custom.setting', userjs.read_text())
        self.assertIn('true); // keep comment', userjs.read_text())
        self.assertEqual(userjs.stat().st_mode & 0o777, 0o600)
        self.assertTrue((active / 'chrome/userChrome.css').is_file())
        self.assertFalse((active.parent / 'old.default/chrome').exists())
        sound = '.local/share/codex-alerts/gong.wav'
        self.assertEqual((self.home / sound).read_bytes(), (REPO / 'home' / sound).read_bytes())
        self.assertNotIn('bcm5974', config.read_text())
        fetch = json.loads((self.home / '.config/fastfetch/config.jsonc').read_text())
        for module in fetch['modules']:
            if isinstance(module, dict) and module.get('type') in ('host', 'cpu'):
                self.assertNotIn('format', module)
        self.assertIn(str(self.home), (self.home / '.config/mpv/mpv.conf').read_text())
        self.assertTrue(os.access(self.home / '.local/bin/touchpad-tapping', os.X_OK))
        dpi = self.home / '.config/xorg/macbookpro-resources'
        dpi.write_text('Xft.dpi: 168\n')
        again = self.command('--apply')
        self.assertIn('restore: 0 files', again.stdout)
        self.assertEqual(dpi.read_text(), 'Xft.dpi: 168\n')
        self.assertEqual(len(list((self.home / '.local/state/dotfiles/backups').iterdir())), 1)
        check = subprocess.run(['i3', '-C', '-c', str(config)], capture_output=True, text=True)
        self.assertEqual(check.returncode, 0, check.stderr)
        build = subprocess.run(['python3', str(self.home / '.local/share/grey-audio-live/live.py'), '--build-only'],
                               capture_output=True, text=True)
        self.assertEqual(build.returncode, 0, build.stderr)

    def test_destination_symlink_aborts_before_any_writes(self):
        outside = Path(self.tmp.name) / 'outside'
        outside.mkdir()
        config = self.home / '.config'
        config.mkdir()
        (config / 'i3').symlink_to(outside, target_is_directory=True)
        result = self.command('--apply', success=False)
        self.assertIn('symlink', result.stderr)
        self.assertFalse((self.home / '.bashrc').exists())
        self.assertEqual(list(outside.iterdir()), [])

    def test_backup_symlink_aborts_before_any_writes(self):
        outside = Path(self.tmp.name) / 'outside'
        outside.mkdir()
        (self.home / '.local/state/dotfiles').mkdir(parents=True)
        (self.home / '.local/state/dotfiles/backups').symlink_to(outside, target_is_directory=True)
        self.command('--apply', success=False)
        self.assertFalse((self.home / '.bashrc').exists())
        self.assertEqual(list(outside.iterdir()), [])

    def test_firefox_ambiguous_defaults_require_explicit_selection(self):
        active = self.firefox()
        with (active.parent / 'profiles.ini').open('a') as stream:
            stream.write('[InstallOTHER]\nDefault=old.default\n')
        self.command('--apply', success=False)
        self.assertFalse((self.home / '.bashrc').exists())
        self.command('--firefox-profile', str(active), '--apply')
        self.assertTrue((active / 'chrome/userChrome.css').is_file())

    def test_profile_requires_portable_restore(self):
        result = subprocess.run(['python3', str(REPO / 'manage.py'), 'snapshot',
                                 '--profile', 'macbookpro11-4'], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)

    def test_installer_preview_does_not_write(self):
        env = dict(os.environ, HOME=str(self.home))
        result = subprocess.run([str(REPO / 'install.sh'), '--align', '--profile', 'macbookpro11-4'],
                                cwd=self.tmp.name, env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_services_wait_for_private_prerequisites(self):
        plan = dict(align.service_plan(self.home))
        self.assertIn('.config/rclone/rclone.conf', plan['rclone-gdrive.service'])
        self.assertIn('.config/isyncrc', plan['aerc-gmail-initialize.service'])
        marker = self.home / '.local/state/aerc-setup/maildir-ready'
        marker.parent.mkdir(parents=True)
        marker.touch()
        for rel in ('.config/aerc/accounts.conf', '.config/isyncrc'):
            path = self.home / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()
        self.assertEqual(dict(align.service_plan(self.home))['aerc-gmail-initialize.service'], [])

    def test_system_settings_back_up_files_without_restarting_logind(self):
        target = Path(self.tmp.name) / 'system/override.conf'
        target.parent.mkdir()
        target.write_bytes(b'old system setting\n')
        target.chmod(0o600)
        backup = Path(self.tmp.name) / 'system-backup'
        with patch.object(align, 'check_profile'), patch.object(align.os, 'geteuid', return_value=0), \
                patch.object(align, 'system_plan', return_value={str(target): b'new system setting\n'}), \
                patch.object(align.subprocess, 'run') as run:
            align.apply_system(self.home, 'macbookpro11-4', True, backup)
        self.assertEqual(target.read_bytes(), b'new system setting\n')
        copies = list(backup.rglob('override.conf'))
        self.assertEqual(len(copies), 1)
        self.assertEqual(copies[0].read_bytes(), b'old system setting\n')
        self.assertEqual(copies[0].stat().st_mode & 0o777, 0o600)
        self.assertFalse(any('restart' in call.args[0] for call in run.call_args_list))

    def test_system_symlink_aborts_before_service_activation(self):
        victim = Path(self.tmp.name) / 'victim'
        victim.write_text('untouched')
        target = Path(self.tmp.name) / 'override.conf'
        target.symlink_to(victim)
        with patch.object(align, 'check_profile'), patch.object(align.os, 'geteuid', return_value=0), \
                patch.object(align, 'system_plan', return_value={str(target): b'replacement'}), \
                patch.object(align.subprocess, 'run') as run:
            with self.assertRaises(SystemExit):
                align.apply_system(self.home, 'macbookpro11-4', True, Path(self.tmp.name) / 'backups')
        run.assert_not_called()
        self.assertEqual(victim.read_text(), 'untouched')


if __name__ == '__main__':
    unittest.main()
