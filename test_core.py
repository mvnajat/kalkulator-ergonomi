import unittest, math, json
from pathlib import Path
from core import parse_observations, statistics, percentiles, cvl, time_comparison, environment_metrics

class CoreTests(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(parse_observations('12.5, 13; 12.8'),[12.5,13,12.8])
    def test_bad_observations(self):
        for text in ['','1','0,1','-1,2','nan,2','inf,2','a,b']:
            with self.subTest(text=text),self.assertRaises(ValueError):parse_observations(text)
    def test_statistics(self):
        s=statistics([10,10,10]);self.assertEqual(s['SD'],0);self.assertEqual(s["N'"],0);self.assertEqual(s['Keseragaman'],'Seragam')
    def test_sd(self):
        self.assertAlmostEqual(statistics([1,2,3])['SD'],1)
        self.assertAlmostEqual(statistics([1,2,3],sample=False)['SD'],math.sqrt(2/3))
    def test_outlier(self):
        self.assertEqual(statistics([12.5,13,12.8,12.4,15.8,12.7,12.9,12.5,12.6,13,12.7,12.8])['Keseragaman'],'Tidak seragam')
    def test_percentiles(self):
        p=percentiles([10,20,30],'Empiris');self.assertEqual(p['P50'],20);self.assertEqual(p['P5'],11)
        p=percentiles([10,10,10],'Otomatis');self.assertIsNone(p['p Shapiro-Wilk']);self.assertEqual(p['P95'],10)
    def test_cvl(self):
        self.assertEqual(cvl(60,120,180),50)
        for args in [(70,100,60),(70,60,180),(60,200,180),(0,60,180)]:
            with self.subTest(args=args),self.assertRaises(ValueError):cvl(*args)
    def test_time(self):
        r=time_comparison(10,60,1,0,15,'Waktu normal')
        self.assertEqual(len(r),3)
        for x in r:self.assertAlmostEqual(x['Wb (detik)'],11.5)
        self.assertAlmostEqual(time_comparison(10,60,1,0,15,'Waktu kerja total')[0]['Wb (detik)'],10/.85)
        self.assertAlmostEqual(time_comparison(10,60,1,20,0,'Waktu normal')[2]['p'],1.2)
    def test_invalid_allowance(self):
        with self.assertRaises(ValueError):time_comparison(10,60,1,0,100,'Waktu normal')
    def test_environment(self):
        r=environment_metrics(10,8,2,120)
        self.assertEqual(r['Selesai (%)'],80);self.assertEqual(r['Kesalahan (%)'],25)
        self.assertEqual(r['Baik terhadap target (%)'],60);self.assertEqual(r['Output baik (unit/jam)'],180)
        self.assertEqual(environment_metrics(10,0,0,120)['Kesalahan (%)'],0)
        with self.assertRaises(ValueError):environment_metrics(10,2,3,120)
    def test_owas(self):
        data=json.loads((Path(__file__).parent/'assets/module_data.json').read_text())
        self.assertEqual(len(data['owas']),252);self.assertEqual(len(data['dimensions']),32)
        self.assertEqual(data['owas']['1111'],1)
        self.assertTrue(all(v in [1,2,3,4] for v in data['owas'].values()))

if __name__=='__main__':unittest.main(verbosity=2)
