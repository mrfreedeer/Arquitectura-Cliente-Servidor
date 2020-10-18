#include <iostream>
#include <vector>
#include <zmqpp/zmqpp.hpp>
#include <string>
#include <sstream>
#include <stdlib.h>     /* for realloc() and free() */
#include <string.h>     /* for memset() */
#include <errno.h>      /* for errno */
#include "nlohmann/json.hpp"
#include <armadillo>
#include <typeinfo>
#include "Threadpool.hh"

using namespace zmqpp;
using namespace arma;
using json = nlohmann::json;

class EWorker{
    private:
        mat r_ic;
        std::vector<mat> cov;
        mat regcov;
        mat mu;
        vec pivector;
        mat data;
    public:
        EWorker(std::vector<std::vector<double>> muvec,
                std::vector<double> piv,
                std::vector<std::vector<double>> regcovvec,
                std::vector<std::vector<std::vector<double>>> covvec,
                std::vector<std::vector<double>> xvec 

                ){
            // int n_of_sources = data.size();
            // int n_of_data = data.at(0).size();
            int counter = 0;
            for (std::vector<double> cmu: muvec){
                mu.insert_cols(counter, vec(cmu));
                counter++;
            }
            pivector = vec(piv);
            counter = 0;
            for (std::vector<double> cregcov: regcovvec){
                regcov.insert_cols(counter, vec(cregcov));
                counter++;
            }
            counter = 0;
            int counter2 = 0;
            for (std::vector<std::vector<double>> covmatrix : covvec){
                mat temp;
                for(std::vector<double>covmatrixrow: covmatrix){
                    temp.insert_cols(counter,vec(covmatrixrow));
                    counter++;
                }
                counter = 0;
                cov.insert(cov.begin() + counter2, temp);
                counter2++;
            }

            // cout<<"MU:\n-------------------\n"<<mu<<"\n-------------------\n";
            // cout<<"PI:\n-------------------\n"<<pivector<<"\n-------------------\n";
            // // cout<<"COV:\n-------------------\n";

            // for (mat covtest : cov)
            //     cout<<covtest<<endl;
            // cout<<"\n-------------------\n";
            for(int i=0;i<xvec.at(0).size();i++){
                std::vector<double>temp(xvec.size());
                counter = 0;
                for(std::vector<double> datarow : xvec){
                    temp.at(counter)= datarow.at(i);
                    counter++;
                }
                data.insert_cols(i, vec(temp));
            }
            // cout<<"\n-------------------\n";

            // cout<<"DATA: "<<endl<<data;
            // cout<<"\n-------------------\n";

            // r_ic = new mat(n_of_data, n_of_sources);
            // cov = new mat(n_of_data, n_of_data);
            // std::cout<<mu<<endl;
        }   
        
        mat& getRIC(){
            // r_ic.zeros();
            mat datatranspose = data.t();
            for(int i = 0; i < mu.n_cols; i++){
                {
                    ThreadPool pool(4);
                    pool.enqueue([i, this, datatranspose]{
                    mat co = cov.at(i);
                    co += regcov;
                    std::vector<double> r(data.n_rows);
                    double detco = det(co);
                    double pic = pivector.at(i);
                    double fraction = 1/sqrt(pow((2*datum::pi), mu.n_rows)* det(co));
                    vec m(mu.colptr(i),mu.n_rows);

                    
                        for(int j = 0; j < datatranspose.n_cols; j++){
                        
                            vec datasubset(datatranspose.colptr(j), datatranspose.n_rows);
                            mat delta = datasubset - m;
                            mat deltatranspose = delta.t();
                            double exparg = ((-0.5)*deltatranspose*inv(co)*delta).eval()(0,0);
                            double eulerexp = exp(exparg);
                            // cout<<"First: "<<(-0.5)*deltatranspose;
                            // cout<<"Second:\n "<<inv(co)*delta<<endl;

                            // cout<<"Fraction: "<<fraction<<"\tExparg: "<<exparg<<"\tEulerexp:"<<eulerexp<<endl;
                            double pdf = eulerexp * fraction;
                            pdf *= pic;
                            r.at(j)=pdf;

                        }
                    r_ic.insert_cols(i,vec(r));
                });
                }
               
            
            }
            
            r_ic = normalise(r_ic,1,1);
            return r_ic;
        }
};

// Lo que debe hacer el worker es:
// 1. Recibir un arreglo de tuplas
// 2. Iterar sobre calcular el arreglo ric para estos datos 
// 3. Enviar Ric al sink

// class EWorker {
//   public:
//     EWorker(std::vector <std::vector <float>> data) {

//     };

//     std::vector <std::vector <float>> obtenerVectorRIC() {
    // """E Step"""
    // r_ic = np.zeros((len(self.X),len(self.cov)))
    // for m,co,p,r in zip(self.mu,self.cov,self.pi,range(len(r_ic[0]))):
    //     co+=self.reg_cov
    //     mn = multivariate_normal(mean=m,cov=co)
    //     r_ic[:,r] = p*mn.pdf(self.X)/np.sum([pi_c*multivariate_normal(mean=mu_c,cov=cov_c).pdf(X) for pi_c,mu_c,cov_c in zip(self.pi,self.mu,self.cov+self.reg_cov)],axis=0)

//     }
// };

// std::vector <std::vector<float>> convertToVector(std::string npArray) {
//     std::vector <float> vec;
//     vec.push_back(1);
//     std::vector <std::vector <float>> vecs;
//     vecs.push_back(vec);
//     return vecs;

// }
int main() {
    context ctx;
    zmqpp::message message;
    socket work(ctx, socket_type::pull);
    socket sink(ctx, socket_type::push);
    std::cout<<"connecting"<<std::endl;
    work.connect("tcp://localhost:5557");
    sink.connect("tcp://localhost:5558");
    std::cout<<"Receiving"<<std::endl;

    while(true){
    work.receive(message);
    json info = json::parse(message.get(0));

    std::cout<<"using json"<<std::endl;
    // std::cout << info["mu"] << std::endl;
    // std::vector<double> armadillotest{10,20,30};
    // mat hi(armadillotest);
    std::vector<std::vector<double>> mu = info["mu"].get <std::vector<std::vector<double>>> ();
    std::vector<double> pi = info["pi"].get <std::vector <double>>();
    std::vector<std::vector<double>> regcov = info["regcov"].get <std::vector<std::vector<double>>> ();
    std::vector<std::vector<std::vector<double>>> cov = info["cov"]
    .get <std::vector<std::vector<std::vector<double>>>> ();
    std::vector<std::vector<double>> x = info["x"].get <std::vector<std::vector<double>>> ();
    // std::cout<<"mu: "<<info["mu"]<<std::endl;
    
    EWorker worker(mu,pi,regcov, cov, x);
    mat  r_ic = worker.getRIC(); 
    std::vector<std::vector <double>> vectosend(x.size());
    for (int i=0; i<r_ic.n_rows;i++){
        vectosend[i]=arma::conv_to<std::vector<double>>::from(r_ic.row(i));
    }
    cout<<"R_IC:\n-------------------\n";

    cout<<r_ic<<endl;

    json tosend;
    tosend["ric"] = vectosend;
    tosend["X"] = x;
    auto t = tosend.dump();
    sink.send(t);
    }
    // std::vector <std::vector <float>> dataAsVector = convertToVector(message.get(0));
    // EWorker worker = EWorker(dataAsVector);
    // std::vector <std::vector <float>> ric = worker.obtenerVectorRIC();
}
