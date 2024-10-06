from NewCanned import *
__SECURITY_SESSION_OPEN__ = True

from uuid import uuid4
import pathlib
from django.utils.crypto import constant_time_compare
from django.contrib.auth.models import Permission
from django.utils.translation import gettext_noop
import binascii
import hashlib
import hmac
import os
from secrets import token_bytes, token_hex
import bcrypt
from django.contrib.auth.hashers import BasePasswordHasher, mask_hash
try:
    from NewCanned.settings import SECRET_PEPPER
except ImportError:
    if input("WARNING: pepper key file not found. Continue (not recommended)? Y/[N] >> ").casefold() != 'y':
        exit(1)
from candb.models import Profile


class PepperedHasher(BasePasswordHasher):
    algorithm = "peppered_pbkdf2_sha384"
    digest = hashlib.sha384
    library = ("bcrypt", "bcrypt")
    rounds = 12

    def salt(self):
        bcrypt = self._load_library()
        return bcrypt.gensalt(self.rounds)

    def encode(self, password: str, salt: bytes):
        bcrypt = self._load_library()
        peppered_password = hmac.new(SECRET_PEPPER, password.encode(), self.digest).digest()
        hashed = bcrypt.hashpw(peppered_password, salt).decode("ascii")
        return "%s$%s" % (self.algorithm, hashed)

    def decode(self, encoded):
        algorithm, empty, algostr, work_factor, data = encoded.split("$", 4)
        assert algorithm == self.algorithm
        return {
            "algorithm": algorithm,
            "algostr": algostr,
            "checksum": data[22:],
            "salt": data[:22],
            "work_factor": int(work_factor),
        }

    def verify(self, password, encoded):
        algorithm, data = encoded.split("$", 1)
        assert algorithm == self.algorithm
        encoded_2 = self.encode(password, data.encode("ascii"))
        return constant_time_compare(encoded, encoded_2)

    def safe_summary(self, encoded):
        decoded = self.decode(encoded)
        return {
            gettext_noop("algorithm"): decoded["algorithm"],
            gettext_noop("work factor"): decoded["work_factor"],
            gettext_noop("salt"): mask_hash(decoded["salt"]),
            gettext_noop("checksum"): mask_hash(decoded["checksum"]),
        }

    def must_update(self, encoded):
        decoded = self.decode(encoded)
        return decoded["work_factor"] != self.rounds

    def harden_runtime(self, password, encoded):
        _, data = encoded.split("$", 1)
        salt = data[:29]  # Length of the salt in bcrypt.
        rounds = data.split("$")[2]
        # work factor is logarithmic, adding one doubles the load.
        diff = 2 ** (self.rounds - int(rounds)) - 1
        while diff > 0:
            self.encode(password, salt.encode("ascii"))
            diff -= 1




def generateNewToken(path: os.PathLike, nbytes: int = None, allowAnyway: bool = False) -> bytes:
    _passerr=False
    if os.path.exists(path) or os.path.isfile(path):
        if allowAnyway:
            print("File already exists. Confirm overwrite? THIS WILL CAUSE ALL DATA TO BE LOST!")
            confirm = token_hex(32)
            if input(f"Type '{confirm}' to confirm delete >> ") == confirm and input("This is your last chance. Continue? [y/N] (case sensitive) > ") == 'y':
                os.chmod(path, 300)
                os.remove(path)
                _passerr=True
            else:
                pass
    else:
        _passerr = True
    if not _passerr:
        raise FileExistsError(
            "\n===STOP! STOP! STOP!===\nDO NOT OVERWRITE PRE-EXISTING PEPPER KEY FILE.\nONCE THE KEY HAS BEEN OVERWRITTEN, "\
            "THE DATA WILL BE PERMANENTLY LOST.\nTHIS INCLUDES ALL HASHED DATA USING THE PEPPER, WHICH WILL BE IRRECOVERABLE.")
    tkn = token_bytes(nbytes)
    with open(path, 'xb') as _f:
        _f.write(tkn)
    with open(pathlib.Path(path).parent / f"PEPPER-BACKUP-{uuid4()}.keybackup", "xb") as _f:
        _f.write(tkn)
    os.chmod(path, 400)
    return tkn


def getAllPermissions():
    return Permission.objects.all()