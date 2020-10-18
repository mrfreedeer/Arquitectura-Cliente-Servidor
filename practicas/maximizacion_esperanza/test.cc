#include <armadillo>

using namespace arma;
using namespace std;

int main(){
    mat data = {1.1,10.10};
    mat mu = {1.1,2.2};
    mat cov = {1.1,1.1};
    mat detTest = {{1,2},{4,5}};
    cout<<normpdf(data,mu,cov)<<endl;
    cout<<normpdf(1.1,1.1,1.1)<<endl;
    cout<<normpdf(10.10,2.2,5.5)<<endl;
    cout<<normpdf(1.1,2.2,5.5)<<endl;
    cout<<normpdf(1.1,mu,cov)<<endl;
    cout<<"-----------------------"<<endl;
    cout<<data<<endl;
    cout<<det(detTest)<<endl;

    return 0;
}