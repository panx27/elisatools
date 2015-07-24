# one-time command to select mt experiments for all europarl data and make original and tok-only versions
for i in bul ces dan deu ell est fin fra hun ita lav lit nld pol por ron slk slv spa swe; do
    # basic experiment
    odir=mockups/$i/mtexp/cdec.isi
    paste mockups/$i/parallel/extracted/tok.cdec/lc/europarl.tok.lc.$i mockups/$i/parallel/extracted/tok.isi/lc/europarl.tok.lc.eng | python /home/nlg-02/LORELEI/ELISA/tools/select_mt_data.py -s $i -t eng -o $odir -l tok.lc --smalllabel 150k --mediumlabel 300k --largelabel 600k;
    # make tok-but-not-lc target training data only
    for j in 150k 300k 600k; do
	sed -f $odir/training.$j.sed mockups/$i/parallel/extracted/tok.isi/europarl.tok.eng > $odir/training.$j.tok.eng;
    done
    # make orig dev 
    for j in dev test; do
	sed -f $odir/$j.sed mockups/$i/parallel/extracted/original/europarl.eng > $odir/$j.eng;
    done
done
