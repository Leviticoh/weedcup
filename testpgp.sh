set -e
testdir='/tmp/testpgp'

mkdir -p "$testdir"
mkdir -p "$testdir/gnupg"
export GNUPGHOME="$testdir/gnupg"

for algo in {rsa,dsa,ed25519};
do
	kname="test-$algo"
	gpg --quick-gen-key --yes --batch --passphrase '' "$kname" "$algo"
	gpg --export "$kname" > "${testdir}/${kname}_pub.pgp"
	gpg --export-secret-key "$kname" > "${testdir}/${kname}_sec.pgp"
	python ./filterkey.py "${testdir}/${kname}_sec.pgp" > "${testdir}/${kname}_sec.ben"
	python ./rebuild_key.py "${testdir}/${kname}_sec.ben" "${testdir}/${kname}_pub.pgp" > "${testdir}/${kname}_rec.pgp"
	sha256sum "${testdir}/${kname}_sec.pgp" "${testdir}/${kname}_rec.pgp" >> "${testdir}/res.log"
done

